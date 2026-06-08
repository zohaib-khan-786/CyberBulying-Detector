"""
Meta Webhook endpoints
GET  /api/webhook/meta   — verification challenge (one-time setup)
POST /api/webhook/meta   — incoming events from Facebook / Instagram
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from typing import List
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models.database import Flag, SessionLocal

webhook_bp = Blueprint("webhook", __name__)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "my_verify_token")
APP_SECRET   = os.getenv("META_APP_SECRET", "")

if not APP_SECRET:
    logger.warning(
        "META_APP_SECRET not set — webhook signature verification DISABLED. "
        "Do not use in production."
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _verify_signature(payload: bytes, sig_header: str) -> bool:
    """Validate X-Hub-Signature-256 header from Meta."""
    if not APP_SECRET or not sig_header:
        return True          # skip in dev if secret not configured
    expected = "sha256=" + hmac.new(
        APP_SECRET.encode(), payload, digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


def _extract_comments(body: dict) -> list[dict]:
    """
    Parse Meta webhook payload and return list of
    {platform, comment_id, text, from_name, timestamp}.

    Handles three event types:
    - Instagram comments:  entry.changes where field == "comments"
    - Facebook page comments: entry.changes where field == "feed"
    - Facebook messages:   entry.messaging where message exists
    """
    comments = []

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            field = change.get("field", "")

            # Instagram comments
            if field == "comments":
                comments.append({
                    "platform":   "instagram",
                    "comment_id": value.get("id"),
                    "text":       value.get("text", ""),
                    "from_name":  value.get("from", {}).get("username", "unknown"),
                    "from_id":    value.get("from", {}).get("id", ""),
                    "timestamp":  value.get("timestamp", int(time.time())),
                })

            # Facebook page comments (comes as "feed" field)
            if field == "feed":
                item = value.get("item", "")
                verb = value.get("verb", "")
                # Only process new comments (not edits, deletes, etc.)
                if item == "comment" and verb == "add":
                    comments.append({
                        "platform":   "facebook",
                        "comment_id": value.get("comment_id") or value.get("post_id"),
                        "text":       value.get("message", ""),
                        "from_name":  value.get("from", {}).get("name", "unknown"),
                        "from_id":    value.get("from", {}).get("id", ""),
                        "timestamp":  value.get("created_time", int(time.time())),
                    })

        # Facebook direct messages
        for msg in entry.get("messaging", []):
            if "message" in msg:
                comments.append({
                    "platform":   "facebook",
                    "comment_id": msg.get("message", {}).get("mid"),
                    "text":       msg.get("message", {}).get("text", ""),
                    "from_name":  msg.get("sender", {}).get("id", "unknown"),
                    "from_id":    msg.get("sender", {}).get("id", ""),
                    "timestamp":  msg.get("timestamp", int(time.time())),
                })

    return comments


# ── Routes ─────────────────────────────────────────────────────────────────────

@webhook_bp.route("/test", methods=["GET"])
def test_webhook():
    """Test endpoint — confirms the webhook route is reachable."""
    logger.info("Webhook test endpoint hit!")
    return jsonify({
        "status": "ok",
        "message": "Webhook route is working",
        "verify_token": VERIFY_TOKEN,
        "app_secret_set": bool(APP_SECRET),
    }), 200


@webhook_bp.route("/debug", methods=["GET"])
def debug_config():
    """Debug endpoint — shows current webhook configuration."""
    logger.info("Debug endpoint hit!")
    return jsonify({
        "verify_token": VERIFY_TOKEN,
        "app_secret_set": bool(APP_SECRET),
        "app_secret_preview": APP_SECRET[:8] + "..." if APP_SECRET else "NOT SET",
        "meta_page_token_set": bool(os.getenv("META_PAGE_ACCESS_TOKEN")),
        "meta_page_id": os.getenv("META_PAGE_ID", "NOT SET"),
        "meta_app_id": os.getenv("META_APP_ID", "NOT SET"),
    }), 200


@webhook_bp.route("/meta", methods=["GET"])
def verify_webhook():
    """Meta calls this once to verify the webhook URL."""
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    logger.info("WEBHOOK VERIFY: mode=%s token=%s challenge=%s", mode, token, challenge)
    logger.info("Expected token: %s", VERIFY_TOKEN)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return challenge, 200
    return jsonify({"error": "Verification failed"}), 403


@webhook_bp.route("/meta", methods=["POST"])
def receive_webhook():
    """Process incoming Facebook / Instagram webhook events."""
    raw = request.get_data()
    sig = request.headers.get("X-Hub-Signature-256", "")

    logger.info("========================================")
    logger.info("WEBHOOK RECEIVED")
    logger.info("Method: %s", request.method)
    logger.info("URL: %s", request.url)
    logger.info("Headers: %s", dict(request.headers))
    logger.info("Body (first 2000 chars): %s", raw[:2000])
    logger.info("Signature: %s", sig[:50] if sig else "NONE")
    logger.info("========================================")

    if not _verify_signature(raw, sig):
        logger.warning("Invalid webhook signature — request rejected.")
        return jsonify({"error": "Bad signature"}), 403

    body = request.get_json(silent=True)
    if not body:
        logger.warning("Could not parse request body as JSON")
        logger.warning("Raw body: %s", raw[:500])
        return jsonify({"error": "Invalid JSON"}), 400

    logger.info("Parsed body: %s", json.dumps(body, indent=2)[:3000])

    clf     = current_app.config["CLASSIFIER"]
    flagged = 0

    comments = _extract_comments(body)
    logger.info("Extracted %d comments from webhook payload", len(comments))

    if len(comments) == 0:
        logger.warning("No comments extracted! Payload structure might be unexpected.")
        logger.warning("Body object type: %s", body.get("object"))
        logger.warning("Body entry count: %d", len(body.get("entry", [])))
        for i, entry in enumerate(body.get("entry", [])):
            logger.warning("Entry %d: changes=%s, messaging=%s", i,
                         len(entry.get("changes", [])), len(entry.get("messaging", [])))
            for j, change in enumerate(entry.get("changes", [])):
                logger.warning("  Change %d: field=%s, value=%s", j,
                             change.get("field"), json.dumps(change.get("value", {}))[:500])

    for comment in comments:
        logger.info("Processing: platform=%s author=%s text=%s",
                     comment["platform"], comment["from_name"], comment["text"][:100])
        if not comment["text"].strip():
            logger.info("Skipping empty comment")
            continue
        result = _process_comment(clf, comment)
        logger.info("Result: label=%s confidence=%.2f harmful=%s",
                     result.get("label"), result.get("confidence", 0), result.get("is_harmful"))
        if result.get("is_harmful"):
            flagged += 1

    logger.info("Webhook done — %d flagged out of %d comments", flagged, len(comments))
    return jsonify({"received": True, "flagged": flagged}), 200


# ── Simulate endpoint (dev/demo only) ─────────────────────────────────────────

@webhook_bp.route("/simulate", methods=["POST"])
def simulate():
    """
    Simulate a webhook event without a real Meta connection.
    Body: {"text": "...", "platform": "instagram", "author": "testuser"}

    NOTE: Does NOT re-route through receive_webhook() — that would require
    patching Flask internals (request._cached_json) which breaks in Flask 3+.
    Instead we call clf.predict() directly and share the same _process_comment
    helper so behaviour is identical.
    """
    data     = request.get_json(silent=True) or {}
    text     = (data.get("text") or "").strip()
    platform = data.get("platform", "instagram")
    author   = data.get("author",   "testuser")

    if not text:
        return jsonify({"error": "Field 'text' is required"}), 400

    comment = {
        "platform":   platform,
        "comment_id": "sim_" + str(int(time.time())),
        "text":       text,
        "from_name":  author,
        "timestamp":  int(time.time()),
    }

    clf    = current_app.config["CLASSIFIER"]
    result = _process_comment(clf, comment)
    return jsonify(result), 200


def _process_comment(clf, comment: dict) -> dict:
    """
    Shared logic: run classifier on a comment dict, persist to DB,
    and return a serialisable result dict.
    Used by both receive_webhook() and simulate().
    All comments are saved (harmful and clean) so they appear in the Live Feed.
    """

    text   = comment["text"].strip()
    result = clf.predict(text)

    payload = {
        **comment,
        **result.to_dict(),
        "auto_flagged": True,
    }

    db = SessionLocal()
    try:
        flag = Flag(
            text          = text,
            label         = result.label,
            label_id      = result.label_id,
            confidence    = result.confidence,
            severity      = result.severity,
            color         = result.color,
            is_harmful    = result.is_harmful,
            trigger_words = json.dumps(result.trigger_words) if result.trigger_words else None,
            source        = comment.get("platform", "webhook"),
            author        = comment.get("from_name", "unknown"),
            author_id     = comment.get("from_id", ""),
            platform      = comment.get("platform"),
            comment_id    = comment.get("comment_id"),
            auto_flagged  = True,
        )
        db.add(flag)
        db.commit()
        db.refresh(flag)
        payload["id"] = flag.id
        if result.is_harmful:
            logger.warning(
                "FLAGGED [%s] from @%s on %s: %.50s…",
                result.label, comment.get("from_name"), comment.get("platform"), text,
            )
    except Exception as exc:
        db.rollback()
        logger.error("DB write failed in _process_comment: %s", exc)
    finally:
        db.close()

    return payload

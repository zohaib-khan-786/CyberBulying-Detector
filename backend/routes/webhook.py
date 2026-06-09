"""
Meta Webhook endpoints — multi-tenant
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
from sqlalchemy.orm import Session

from models.database import (
    Flag, MetaCredentials, SessionLocal, Tenant, TimeSeriesPoint,
)
from models.classifier import CyberbullyingClassifier, PredictionResult

webhook_bp = Blueprint("webhook", __name__)
logger = logging.getLogger(__name__)


def _get_tenant_for_page(page_id: str) -> tuple[Tenant | None, MetaCredentials | None]:
    """Find which tenant owns this page_id."""
    db = SessionLocal()
    try:
        creds = db.query(MetaCredentials).filter(
            MetaCredentials.page_id == page_id,
            MetaCredentials.is_active == True,
        ).first()
        if creds:
            tenant = db.query(Tenant).filter(Tenant.id == creds.tenant_id).first()
            return tenant, creds
        return None, None
    finally:
        db.close()


def _get_creds_for_verify_token(verify_token: str) -> MetaCredentials | None:
    """Find credentials by webhook verify token (fallback)."""
    db = SessionLocal()
    try:
        return db.query(MetaCredentials).filter(
            MetaCredentials.webhook_verify_token == verify_token,
            MetaCredentials.is_active == True,
        ).first()
    finally:
        db.close()


def _verify_signature(payload: bytes, sig_header: str, app_secret: str) -> bool:
    """Validate X-Hub-Signature-256 header from Meta."""
    if not app_secret or not sig_header:
        return True  # skip if no secret configured
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload, digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


def _extract_comments(body: dict) -> list[dict]:
    """Parse Meta webhook payload into comment dicts."""
    comments = []

    for entry in body.get("entry", []):
        # Page ID from the entry — used for tenant routing
        page_id = entry.get("id", "")

        for change in entry.get("changes", []):
            value = change.get("value", {})
            field = change.get("field", "")

            if field == "comments":
                comments.append({
                    "platform":   "instagram",
                    "page_id":    page_id,
                    "comment_id": value.get("id"),
                    "text":       value.get("text", ""),
                    "from_name":  value.get("from", {}).get("username", "unknown"),
                    "from_id":    value.get("from", {}).get("id", ""),
                    "timestamp":  value.get("timestamp", int(time.time())),
                })

            if field == "feed":
                item = value.get("item", "")
                verb = value.get("verb", "")
                if item == "comment" and verb == "add":
                    comments.append({
                        "platform":   "facebook",
                        "page_id":    page_id,
                        "comment_id": value.get("comment_id") or value.get("post_id"),
                        "text":       value.get("message", ""),
                        "from_name":  value.get("from", {}).get("name", "unknown"),
                        "from_id":    value.get("from", {}).get("id", ""),
                        "timestamp":  value.get("created_time", int(time.time())),
                    })

        for msg in entry.get("messaging", []):
            if "message" in msg:
                comments.append({
                    "platform":   "facebook",
                    "page_id":    page_id,
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
    token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "my_verify_token")
    return jsonify({
        "status": "ok",
        "message": "Webhook route is working",
        "verify_token": token,
    }), 200


@webhook_bp.route("/debug", methods=["GET"])
def debug_config():
    """Debug endpoint — shows current webhook configuration."""
    token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
    return jsonify({
        "verify_token": token,
        "note": "Multi-tenant: page IDs are routed to their owning tenant via meta_credentials table",
    }), 200


@webhook_bp.route("/meta", methods=["GET"])
def verify_webhook():
    """Meta calls this once to verify the webhook URL."""
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    logger.info("WEBHOOK VERIFY: mode=%s token=%s", mode, token)

    # Try to find credentials with this verify token
    creds = _get_creds_for_verify_token(token)
    expected = creds.webhook_verify_token if creds else os.getenv("META_WEBHOOK_VERIFY_TOKEN", "my_verify_token")

    if mode == "subscribe" and token == expected:
        logger.info("Webhook verified for tenant %s.", creds.tenant_id if creds else "default")
        return challenge, 200
    return jsonify({"error": "Verification failed"}), 403


@webhook_bp.route("/meta", methods=["POST"])
def receive_webhook():
    """Process incoming Facebook / Instagram webhook events — multi-tenant."""
    raw = request.get_data()
    sig = request.headers.get("X-Hub-Signature-256", "")
    body = request.get_json(silent=True) or {}

    logger.info("WEBHOOK RECEIVED — body keys: %s", list(body.keys()))

    # Find tenant from the first entry's page ID
    entry = (body.get("entry") or [{}])[0]
    page_id = entry.get("id", "")

    tenant, creds = _get_tenant_for_page(page_id)
    if not tenant or not creds:
        logger.warning("No tenant found for page_id=%s. Dropping webhook.", page_id)
        return jsonify({"received": True}), 200  # silent ack

    # Verify signature using this tenant's app_secret
    app_secret = creds.app_secret or ""
    if not _verify_signature(raw, sig, app_secret):
        logger.warning("Invalid webhook signature for tenant %d — rejected.", tenant.id)
        return jsonify({"error": "Bad signature"}), 403

    clf = current_app.config["CLASSIFIER"]
    comments = _extract_comments(body)
    flagged = 0
    db = SessionLocal()

    try:
        for comment in comments:
            text = comment.get("text", "").strip()
            if not text:
                continue

            result = clf.predict(text)

            flag = Flag(
                tenant_id    = tenant.id,
                text         = text,
                label        = result.label,
                label_id     = result.label_id,
                confidence   = result.confidence,
                severity     = result.severity,
                color        = result.color,
                is_harmful   = result.is_harmful,
                source       = comment.get("platform", "webhook"),
                author       = comment.get("from_name", "unknown"),
                author_id    = comment.get("from_id", ""),
                platform     = comment.get("platform"),
                comment_id   = comment.get("comment_id"),
                auto_flagged = True,
            )
            db.add(flag)

            if result.is_harmful:
                flagged += 1
                logger.warning(
                    "FLAGGED [%s] tenant=%d @%s: %.50s",
                    result.label, tenant.id, comment.get("from_name"), text,
                )

        db.commit()
        logger.info("Webhook done — %d flagged out of %d for tenant %d", flagged, len(comments), tenant.id)
    except Exception as exc:
        db.rollback()
        logger.exception("Webhook processing failed: %s", exc)
    finally:
        db.close()

    return jsonify({"received": True, "flagged": flagged}), 200


@webhook_bp.route("/simulate", methods=["POST"])
def simulate():
    """Simulate a webhook event without a real Meta connection."""
    data     = request.get_json(silent=True) or {}
    text     = (data.get("text") or "").strip()
    platform = data.get("platform", "instagram")
    author   = data.get("author", "testuser")
    tenant_id = data.get("tenant_id")

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
    result = clf.predict(text)

    # Find a tenant to associate (default to first if not specified)
    db = SessionLocal()
    try:
        if tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        else:
            tenant = db.query(Tenant).first()

        if not tenant:
            return jsonify({"error": "No tenant found"}), 400

        flag = Flag(
            tenant_id    = tenant.id,
            text         = text,
            label        = result.label,
            label_id     = result.label_id,
            confidence   = result.confidence,
            severity     = result.severity,
            color        = result.color,
            is_harmful   = result.is_harmful,
            source       = platform,
            author       = author,
            comment_id   = comment["comment_id"],
            auto_flagged = True,
        )
        db.add(flag)
        db.commit()
        db.refresh(flag)

        return jsonify({
            "id": flag.id,
            **comment,
            **result.to_dict(),
            "tenant_id": tenant.id,
        }), 200
    except Exception as exc:
        db.rollback()
        logger.exception("Simulate failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()

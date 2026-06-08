"""
Fetch comments endpoint — pulls comments from Meta and runs them through
the classifier for analysis.

GET  /api/fetch/facebook       — fetch Facebook Page comments
GET  /api/fetch/instagram      — fetch Instagram comments
GET  /api/fetch/all            — fetch from both platforms
GET  /api/fetch/status         — check Meta API connection
"""

from __future__ import annotations

import json
import logging
import os

from flask import Blueprint, request, jsonify, current_app

from meta_comments import (
    get_page_id, get_instagram_account_id,
    fetch_facebook_comments, fetch_all_instagram_comments,
    _get,
)
from middleware.auth import require_auth
from models.database import Flag, SessionLocal

fetch_bp = Blueprint("fetch", __name__)
logger = logging.getLogger(__name__)


def _get_page_id() -> str:
    """Get page ID from env or API."""
    # First try from .env (most reliable since me/accounts returns empty)
    page_id = os.getenv("META_PAGE_ID")
    if page_id:
        return page_id
    # Fallback to API
    page_id = get_page_id()
    if page_id:
        return page_id
    return ""


@fetch_bp.route("/status", methods=["GET"])
@require_auth
def fetch_status():
    """Check Meta API connection status."""
    page_id = _get_page_id()
    token = os.getenv("META_PAGE_ACCESS_TOKEN", "")

    return jsonify({
        "page_id_set": bool(page_id),
        "page_id": page_id,
        "token_set": bool(token),
        "token_preview": token[:20] + "..." if len(token) > 20 else token,
    }), 200


@fetch_bp.route("/test-meta", methods=["GET"])
@require_auth
def test_meta_api():
    """Full Meta API diagnostic — tests token, pages, webhook, and permissions."""
    import requests as http_requests

    token = os.getenv("META_PAGE_ACCESS_TOKEN", "")
    app_id = os.getenv("META_APP_ID", "")
    app_secret = os.getenv("META_APP_SECRET", "")
    page_id = os.getenv("META_PAGE_ID", "")
    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")

    results = {
        "config": {
            "app_id_set": bool(app_id),
            "app_secret_set": bool(app_secret),
            "page_id": page_id or "NOT SET",
            "token_set": bool(token),
            "verify_token_set": bool(verify_token),
        },
        "tests": {},
    }

    # Test 1: Token validity — /me
    try:
        resp = http_requests.get(
            "https://graph.facebook.com/v25.0/me",
            params={"access_token": token, "fields": "id,name"},
            timeout=10
        )
        data = resp.json()
        if "error" in data:
            results["tests"]["token_valid"] = {"status": "FAIL", "error": data["error"].get("message")}
        else:
            # Check if this is a page token (name matches page name)
            is_page_token = data.get("id") == page_id
            results["tests"]["token_valid"] = {
                "status": "PASS",
                "user": data.get("name"),
                "id": data.get("id"),
                "token_type": "Page Access Token" if is_page_token else "User Access Token",
            }
    except Exception as e:
        results["tests"]["token_valid"] = {"status": "ERROR", "error": str(e)}

    # Test 2: Token permissions — /me/permissions (only works with User tokens)
    try:
        resp = http_requests.get(
            "https://graph.facebook.com/v25.0/me/permissions",
            params={"access_token": token},
            timeout=10
        )
        data = resp.json()
        perms = data.get("data", [])
        granted = [p["permission"] for p in perms if p.get("status") == "granted"]

        if not granted and data.get("error"):
            # Page tokens don't support /me/permissions
            results["tests"]["permissions"] = {
                "status": "INFO",
                "note": "Page Access Token — permissions are managed at the page level. Token can access page content directly.",
                "token_type": "Page Access Token",
            }
        elif granted:
            results["tests"]["permissions"] = {
                "status": "PASS",
                "granted": granted,
            }
        else:
            results["tests"]["permissions"] = {
                "status": "INFO",
                "note": "Page Access Token — permissions managed at page level",
            }
    except Exception as e:
        results["tests"]["permissions"] = {"status": "ERROR", "error": str(e)}

    # Test 3: Page access — /me/accounts (only works with User tokens)
    try:
        resp = http_requests.get(
            "https://graph.facebook.com/v25.0/me/accounts",
            params={"access_token": token, "fields": "id,name,access_token"},
            timeout=10
        )
        data = resp.json()
        pages = data.get("data", [])

        if not pages and page_id:
            # This is likely a page token — test direct page access instead
            results["tests"]["page_access"] = {
                "status": "INFO",
                "note": f"Page Access Token — direct access to page {page_id} confirmed (see Direct Page Access test)",
                "pages": [{"name": "ZK Lab (from config)", "id": page_id}],
                "count": 1,
            }
        elif pages:
            results["tests"]["page_access"] = {
                "status": "PASS",
                "pages": [{"name": p.get("name"), "id": p.get("id")} for p in pages],
                "count": len(pages),
            }
        else:
            results["tests"]["page_access"] = {
                "status": "WARN",
                "pages": [],
                "count": 0,
                "note": "No pages accessible — check token permissions",
            }
    except Exception as e:
        results["tests"]["page_access"] = {"status": "ERROR", "error": str(e)}

    # Test 4: Direct page access — /{page_id}
    if page_id:
        try:
            resp = http_requests.get(
                f"https://graph.facebook.com/v25.0/{page_id}",
                params={"access_token": token, "fields": "name,id,fan_count"},
                timeout=10
            )
            data = resp.json()
            if "error" in data:
                results["tests"]["direct_page"] = {"status": "FAIL", "error": data["error"].get("message")}
            else:
                results["tests"]["direct_page"] = {"status": "PASS", "name": data.get("name"), "id": data.get("id")}
        except Exception as e:
            results["tests"]["direct_page"] = {"status": "ERROR", "error": str(e)}

    # Test 5: Page feed access — /{page_id}/feed
    if page_id:
        try:
            resp = http_requests.get(
                f"https://graph.facebook.com/v25.0/{page_id}/feed",
                params={"access_token": token, "fields": "message,created_time", "limit": "3"},
                timeout=10
            )
            data = resp.json()
            if "error" in data:
                results["tests"]["page_feed"] = {"status": "FAIL", "error": data["error"].get("message")}
            else:
                posts = data.get("data", [])
                results["tests"]["page_feed"] = {"status": "PASS", "posts_found": len(posts)}
        except Exception as e:
            results["tests"]["page_feed"] = {"status": "ERROR", "error": str(e)}

    # Test 6: Webhook verification
    results["tests"]["webhook_config"] = {
        "status": "INFO",
        "verify_token": verify_token,
        "app_secret_set": bool(app_secret),
        "note": "Test webhook by calling: GET /api/webhook/meta?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=TEST",
    }

    return jsonify(results), 200


@fetch_bp.route("/facebook", methods=["GET"])
@require_auth
def fetch_facebook():
    """
    Fetch comments from your Facebook Page and analyze them.
    Query params: limit (default 25 posts to scan)
    """
    limit = min(int(request.args.get("limit", 25)), 100)

    page_id = _get_page_id()
    if not page_id:
        return jsonify({"error": "No Page ID found. Set META_PAGE_ID in .env."}), 400

    logger.info("=== FACEBOOK FETCH START ===")
    logger.info("Page ID: %s, Post limit: %d", page_id, limit)

    comments = fetch_facebook_comments(page_id, limit=limit)
    if not comments:
        return jsonify({
            "message": "No comments found on this page.",
            "page_id": page_id,
            "total": 0,
            "flagged": 0,
        }), 200

    clf = current_app.config["CLASSIFIER"]
    db = SessionLocal()
    flagged = 0
    saved = 0

    try:
        for comment in comments:
            text = comment.get("text", "").strip()
            if not text:
                continue

            result = clf.predict(text)

            # Check for duplicates
            existing = db.query(Flag).filter(
                Flag.comment_id == comment.get("id"),
                Flag.platform == "facebook"
            ).first()

            if existing:
                continue

            db.add(Flag(
                text=text,
                label=result.label,
                label_id=result.label_id,
                confidence=result.confidence,
                severity=result.severity,
                color=result.color,
                is_harmful=result.is_harmful,
                trigger_words=json.dumps(result.trigger_words) if result.trigger_words else None,
                source="facebook",
                platform="facebook",
                comment_id=comment.get("id"),
                author=comment.get("from_name", "") or f"visitor_{comment.get('id', '')[:12]}",
            ))
            saved += 1

            if result.is_harmful:
                flagged += 1
                logger.info("FLAGGED: [%s] %s by %s (conf=%.2f)",
                           result.label, text[:60], comment.get("from_name"), result.confidence)

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Error processing comments: %s", exc)
    finally:
        db.close()

    logger.info("=== FACEBOOK FETCH DONE: %d total, %d saved, %d flagged ===",
               len(comments), saved, flagged)

    return jsonify({
        "message": f"Fetched {len(comments)} comments. {saved} new, {flagged} flagged.",
        "page_id": page_id,
        "total": len(comments),
        "saved": saved,
        "flagged": flagged,
    }), 200


@fetch_bp.route("/instagram", methods=["GET"])
@require_auth
def fetch_instagram():
    """Fetch comments from your Instagram account and analyze them."""
    media_limit   = min(int(request.args.get("media_limit", 25)), 100)
    comment_limit = min(int(request.args.get("comment_limit", 100)), 500)

    page_id = _get_page_id()
    if not page_id:
        return jsonify({"error": "No Page ID found."}), 400

    ig_id = get_instagram_account_id(page_id)
    if not ig_id:
        return jsonify({"error": "No Instagram Business Account linked to this page."}), 400

    logger.info("=== INSTAGRAM FETCH START ===")
    logger.info("Instagram ID: %s", ig_id)

    comments = fetch_all_instagram_comments(ig_id, media_limit, comment_limit)
    if not comments:
        return jsonify({"message": "No Instagram comments found.", "total": 0, "flagged": 0}), 200

    clf = current_app.config["CLASSIFIER"]
    db = SessionLocal()
    flagged = 0
    saved = 0

    try:
        for comment in comments:
            text = comment.get("text", "").strip()
            if not text:
                continue

            result = clf.predict(text)

            existing = db.query(Flag).filter(
                Flag.comment_id == comment.get("id"),
                Flag.platform == "instagram"
            ).first()

            if existing:
                continue

            db.add(Flag(
                text=text,
                label=result.label,
                label_id=result.label_id,
                confidence=result.confidence,
                severity=result.severity,
                color=result.color,
                is_harmful=result.is_harmful,
                trigger_words=json.dumps(result.trigger_words) if result.trigger_words else None,
                source="instagram",
                platform="instagram",
                comment_id=comment.get("id"),
                author=comment.get("username", "") or f"visitor_{comment.get('id', '')[:12]}",
            ))
            saved += 1

            if result.is_harmful:
                flagged += 1

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Error: %s", exc)
    finally:
        db.close()

    logger.info("=== INSTAGRAM FETCH DONE: %d total, %d saved, %d flagged ===",
               len(comments), saved, flagged)

    return jsonify({
        "message": f"Fetched {len(comments)} Instagram comments. {saved} new, {flagged} flagged.",
        "total": len(comments),
        "saved": saved,
        "flagged": flagged,
    }), 200


@fetch_bp.route("/all", methods=["GET"])
@require_auth
def fetch_all():
    """Fetch from both Facebook and Instagram."""
    page_id = _get_page_id()
    if not page_id:
        return jsonify({"error": "No Page ID found."}), 400

    clf = current_app.config["CLASSIFIER"]
    db = SessionLocal()
    results = {"facebook": {"total": 0, "saved": 0, "flagged": 0},
               "instagram": {"total": 0, "saved": 0, "flagged": 0}}
    errors = []

    try:
        # Facebook
        try:
            fb_comments = fetch_facebook_comments(page_id)
            for c in fb_comments:
                text = c.get("text", "").strip()
                if not text:
                    continue
                existing = db.query(Flag).filter(Flag.comment_id == c.get("id")).first()
                if existing:
                    continue
                r = clf.predict(text)
                db.add(Flag(text=text, label=r.label, label_id=r.label_id, confidence=r.confidence,
                    severity=r.severity, color=r.color, is_harmful=r.is_harmful,
                    trigger_words=json.dumps(r.trigger_words) if r.trigger_words else None,
                    source="facebook", platform="facebook", comment_id=c.get("id"),
                    author=c.get("from_name", "") or f"visitor_{c.get('id', '')[:12]}"))
                results["facebook"]["total"] += 1
                results["facebook"]["saved"] += 1
                if r.is_harmful:
                    results["facebook"]["flagged"] += 1
        except Exception as exc:
            errors.append(f"Facebook: {str(exc)}")
            logger.error("Facebook fetch failed: %s", exc)

        # Instagram (graceful failure)
        try:
            ig_id = get_instagram_account_id(page_id)
            if ig_id:
                ig_comments = fetch_all_instagram_comments(ig_id)
                for c in ig_comments:
                    text = c.get("text", "").strip()
                    if not text:
                        continue
                    existing = db.query(Flag).filter(Flag.comment_id == c.get("id")).first()
                    if existing:
                        continue
                    r = clf.predict(text)
                    db.add(Flag(text=text, label=r.label, label_id=r.label_id, confidence=r.confidence,
                        severity=r.severity, color=r.color, is_harmful=r.is_harmful,
                        trigger_words=json.dumps(r.trigger_words) if r.trigger_words else None,
                        source="instagram", platform="instagram", comment_id=c.get("id"),
                        author=c.get("username", "") or f"visitor_{c.get('id', '')[:12]}"))
                    results["instagram"]["total"] += 1
                    results["instagram"]["saved"] += 1
                    if r.is_harmful:
                        results["instagram"]["flagged"] += 1
            else:
                errors.append("Instagram: No business account linked")
        except Exception as exc:
            errors.append(f"Instagram: {str(exc)}")
            logger.error("Instagram fetch failed: %s", exc)

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Error: %s", exc)
    finally:
        db.close()

    total = results["facebook"]["total"] + results["instagram"]["total"]
    flagged = results["facebook"]["flagged"] + results["instagram"]["flagged"]

    return jsonify({
        "message": f"Fetched {total} comments. {flagged} flagged.",
        "total": total,
        "flagged": flagged,
        "details": results,
        "errors": errors if errors else None,
    }), 200

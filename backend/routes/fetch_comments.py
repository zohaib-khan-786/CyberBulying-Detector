"""
Fetch comments endpoint — pulls comments from Meta and runs them through
the classifier for analysis. Uses per-tenant Meta credentials.
"""

from __future__ import annotations

import json
import logging

from flask import Blueprint, request, jsonify, current_app, g

from meta_comments import (
    get_instagram_account_id,
    fetch_facebook_comments, fetch_all_instagram_comments,
)
from middleware.auth import require_auth, require_admin
from models.database import Flag, MetaCredentials, SessionLocal

fetch_bp = Blueprint("fetch", __name__)
logger = logging.getLogger(__name__)


def _get_creds() -> MetaCredentials | None:
    """Get active Meta credentials for the current user's tenant."""
    tenant_id = g.current_user.tenant_id
    if not tenant_id:
        return None
    db = SessionLocal()
    try:
        return db.query(MetaCredentials).filter(
            MetaCredentials.tenant_id == tenant_id,
            MetaCredentials.is_active == True,
        ).first()
    finally:
        db.close()


@fetch_bp.route("/status", methods=["GET"])
@require_auth
@require_admin
def fetch_status():
    """Check Meta API connection status for current tenant."""
    creds = _get_creds()

    return jsonify({
        "configured": bool(creds and creds.page_access_token),
        "page_id": creds.page_id if creds else "NOT SET",
        "has_token": bool(creds and creds.page_access_token),
        "has_ig_account": bool(creds and creds.instagram_account_id),
    }), 200


@fetch_bp.route("/facebook", methods=["GET"])
@require_auth
@require_admin
def fetch_facebook():
    """Fetch comments from your Facebook Page and analyze them."""
    limit = min(int(request.args.get("limit", 25)), 100)

    creds = _get_creds()
    if not creds or not creds.page_access_token:
        return jsonify({"error": "Meta credentials not configured. Go to Settings first."}), 400
    if not creds.page_id:
        return jsonify({"error": "No Page ID configured."}), 400

    logger.info("=== FACEBOOK FETCH START (tenant %d) ===", g.current_user.tenant_id)

    comments = fetch_facebook_comments(creds.page_id, creds.page_access_token, limit=limit)
    if not comments:
        return jsonify({
            "message": "No comments found on this page.",
            "page_id": creds.page_id,
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

            existing = db.query(Flag).filter(
                Flag.comment_id == comment.get("id"),
                Flag.platform == "facebook",
                Flag.tenant_id == g.current_user.tenant_id,
            ).first()

            if existing:
                continue

            db.add(Flag(
                tenant_id=g.current_user.tenant_id,
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
        "page_id": creds.page_id,
        "total": len(comments),
        "saved": saved,
        "flagged": flagged,
    }), 200


@fetch_bp.route("/instagram", methods=["GET"])
@require_auth
@require_admin
def fetch_instagram():
    """Fetch comments from your Instagram account and analyze them."""
    media_limit   = min(int(request.args.get("media_limit", 25)), 100)
    comment_limit = min(int(request.args.get("comment_limit", 100)), 500)

    creds = _get_creds()
    if not creds or not creds.page_access_token:
        return jsonify({"error": "Meta credentials not configured. Go to Settings first."}), 400
    if not creds.page_id:
        return jsonify({"error": "No Page ID configured."}), 400

    ig_id = creds.instagram_account_id
    if not ig_id:
        ig_id = get_instagram_account_id(creds.page_id, creds.page_access_token)
        if ig_id:
            # Cache it
            db = SessionLocal()
            try:
                c = db.query(MetaCredentials).filter(MetaCredentials.id == creds.id).first()
                if c:
                    c.instagram_account_id = ig_id
                    db.commit()
            finally:
                db.close()

    if not ig_id:
        return jsonify({"error": "No Instagram Business Account linked to this page."}), 400

    logger.info("=== INSTAGRAM FETCH START (tenant %d) ===", g.current_user.tenant_id)

    comments = fetch_all_instagram_comments(ig_id, creds.page_access_token, media_limit, comment_limit)
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
                Flag.platform == "instagram",
                Flag.tenant_id == g.current_user.tenant_id,
            ).first()

            if existing:
                continue

            db.add(Flag(
                tenant_id=g.current_user.tenant_id,
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
@require_admin
def fetch_all():
    """Fetch from both Facebook and Instagram."""
    creds = _get_creds()
    if not creds or not creds.page_access_token:
        return jsonify({"error": "Meta credentials not configured."}), 400

    clf = current_app.config["CLASSIFIER"]
    db = SessionLocal()
    results = {"facebook": {"total": 0, "saved": 0, "flagged": 0},
               "instagram": {"total": 0, "saved": 0, "flagged": 0}}
    errors = []

    try:
        # Facebook
        try:
            fb_comments = fetch_facebook_comments(creds.page_id, creds.page_access_token)
            for c in fb_comments:
                text = c.get("text", "").strip()
                if not text:
                    continue
                existing = db.query(Flag).filter(
                    Flag.comment_id == c.get("id"),
                    Flag.tenant_id == g.current_user.tenant_id,
                ).first()
                if existing:
                    continue
                r = clf.predict(text)
                db.add(Flag(tenant_id=g.current_user.tenant_id, text=text, label=r.label,
                    label_id=r.label_id, confidence=r.confidence, severity=r.severity,
                    color=r.color, is_harmful=r.is_harmful,
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

        # Instagram
        try:
            ig_id = creds.instagram_account_id
            if not ig_id:
                ig_id = get_instagram_account_id(creds.page_id, creds.page_access_token)
            if ig_id:
                ig_comments = fetch_all_instagram_comments(ig_id, creds.page_access_token)
                for c in ig_comments:
                    text = c.get("text", "").strip()
                    if not text:
                        continue
                    existing = db.query(Flag).filter(
                        Flag.comment_id == c.get("id"),
                        Flag.tenant_id == g.current_user.tenant_id,
                    ).first()
                    if existing:
                        continue
                    r = clf.predict(text)
                    db.add(Flag(tenant_id=g.current_user.tenant_id, text=text, label=r.label,
                        label_id=r.label_id, confidence=r.confidence, severity=r.severity,
                        color=r.color, is_harmful=r.is_harmful,
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

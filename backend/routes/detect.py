"""
Detection endpoints
POST /api/detect/text       — single text analysis
POST /api/detect/batch      — analyse up to 50 texts at once
GET  /api/detect/all-flags  — all flags for Live Feed (tenant-scoped)
GET  /api/detect/history    — paginated flagged texts from DB (tenant-scoped)
"""

from __future__ import annotations

import json
import time
import logging
from flask import Blueprint, request, jsonify, current_app, g

from models.database import Flag, SessionLocal
from middleware.auth import require_auth

detect_bp = Blueprint("detect", __name__)
logger    = logging.getLogger(__name__)


def _get_clf():
    return current_app.config["CLASSIFIER"]


def _get_tenant_id() -> int | None:
    """Get tenant_id from current user if authenticated."""
    user = getattr(g, "current_user", None)
    return user.tenant_id if user else None


def _save_flag(result, source: str, author: str, platform: str | None = None) -> Flag | None:
    db = SessionLocal()
    try:
        flag = Flag(
            tenant_id     = _get_tenant_id(),
            text          = result.text,
            label         = result.label,
            label_id      = result.label_id,
            confidence    = result.confidence,
            severity      = result.severity,
            color         = result.color,
            is_harmful    = result.is_harmful,
            trigger_words = json.dumps(result.trigger_words) if result.trigger_words else None,
            source        = source,
            author        = author,
            platform      = platform,
        )
        db.add(flag)
        db.commit()
        db.refresh(flag)
        return flag
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save flag to DB: %s", exc)
        return None
    finally:
        db.close()


@detect_bp.route("/text", methods=["POST"])
def detect_text():
    data   = request.get_json(silent=True) or {}
    text   = (data.get("text") or "").strip()
    source = data.get("source", "manual")
    author = data.get("author", "anonymous")

    if not text:
        return jsonify({"error": "Field 'text' is required and must not be empty"}), 400
    if len(text) > 5000:
        return jsonify({"error": "Text exceeds 5 000 character limit"}), 400

    clf    = _get_clf()
    result = clf.predict(text)
    payload = result.to_dict()
    payload["timestamp"] = int(time.time())
    payload["source"]    = source
    payload["author"]    = author

    if result.is_harmful:
        flag = _save_flag(result, source=source, author=author)
        if flag:
            payload["id"] = flag.id

    return jsonify(payload), 200


@detect_bp.route("/batch", methods=["POST"])
def detect_batch():
    data  = request.get_json(silent=True) or {}
    items = data.get("items", [])

    if not isinstance(items, list):
        return jsonify({"error": "'items' must be a list of strings or objects"}), 400
    if len(items) > 50:
        return jsonify({"error": "Batch limit is 50 items"}), 400

    clf    = _get_clf()
    output = []

    for orig in items:
        text   = (orig.get("text") or "").strip() if isinstance(orig, dict) else str(orig).strip()
        source = (orig.get("source", "batch")     if isinstance(orig, dict) else "batch")
        author = (orig.get("author", "unknown")   if isinstance(orig, dict) else "unknown")

        result  = clf.predict(text)
        payload = result.to_dict()
        payload.update({"timestamp": int(time.time()), "source": source, "author": author})

        if result.is_harmful:
            flag = _save_flag(result, source=source, author=author)
            if flag:
                payload["id"] = flag.id

        output.append(payload)

    harmful_count = sum(1 for p in output if p.get("is_harmful"))
    return jsonify({"total": len(output), "harmful_count": harmful_count, "results": output}), 200


@detect_bp.route("/all-flags", methods=["GET"])
@require_auth
def get_all_flags():
    """Get ALL flags (harmful + clean) for Live Feed — tenant-scoped."""
    page            = int(request.args.get("page", 1))
    per_page        = min(int(request.args.get("per_page", 20)), 100)
    label_filter    = request.args.get("label")
    platform_filter = request.args.get("platform")
    tenant_id       = _get_tenant_id()

    db = SessionLocal()
    try:
        q = db.query(Flag).filter(
            (Flag.mod_action != "delete") | (Flag.mod_action.is_(None))
        )
        if tenant_id:
            q = q.filter(Flag.tenant_id == tenant_id)
        if label_filter and label_filter != "all":
            q = q.filter(Flag.label == label_filter)
        if platform_filter and platform_filter != "all":
            q = q.filter(Flag.platform == platform_filter)

        total = q.count()
        flags = q.order_by(Flag.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({
            "total": total, "page": page, "per_page": per_page,
            "items": [f.to_dict() for f in flags],
        }), 200
    finally:
        db.close()


@detect_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    page            = int(request.args.get("page", 1))
    per_page        = min(int(request.args.get("per_page", 20)), 100)
    label_filter    = request.args.get("label")
    severity_filter = request.args.get("severity")
    tenant_id       = _get_tenant_id()

    db = SessionLocal()
    try:
        q = db.query(Flag).filter(Flag.is_harmful == True)
        if tenant_id:
            q = q.filter(Flag.tenant_id == tenant_id)
        if label_filter:
            q = q.filter(Flag.label == label_filter)
        if severity_filter:
            q = q.filter(Flag.severity == severity_filter)

        total = q.count()
        flags = q.order_by(Flag.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            "page": page, "per_page": per_page, "total": total,
            "items": [f.to_dict() for f in flags],
        }), 200
    finally:
        db.close()

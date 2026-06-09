"""
Moderation endpoints — tenant-scoped.
Manager users can view (GET) but cannot perform actions (POST).
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, current_app, g, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import Flag, ModeratedUser, MetaCredentials, SessionLocal
from middleware.auth import require_auth, require_admin, require_role
from meta_api import delete_comment

moderation_bp = Blueprint("moderation", __name__)
logger = logging.getLogger(__name__)

VALID_ACTIONS = {"delete", "warn", "block", "dismiss"}
WARN_THRESHOLD = 2
BLOCK_THRESHOLD = 4


def _tenant_filter(q, model=None):
    """Scope query to current user's tenant."""
    m = model or Flag
    if g.current_user.tenant_id:
        return q.filter(m.tenant_id == g.current_user.tenant_id)
    return q


def _get_creds(db) -> MetaCredentials | None:
    """Get tenant Meta credentials."""
    if not g.current_user.tenant_id:
        return None
    return db.query(MetaCredentials).filter(
        MetaCredentials.tenant_id == g.current_user.tenant_id,
        MetaCredentials.is_active == True,
    ).first()


# ── Perform a moderation action ────────────────────────────────────────────────

@moderation_bp.route("/action", methods=["POST"])
@require_auth
@require_admin
def take_action():
    data    = request.get_json(silent=True) or {}
    flag_id = data.get("flag_id")
    action  = (data.get("action") or "").lower()
    note    = data.get("note", "")
    admin   = g.current_user.username

    if not flag_id:
        return jsonify({"error": "'flag_id' is required"}), 400
    if action not in VALID_ACTIONS:
        return jsonify({"error": f"'action' must be one of {sorted(VALID_ACTIONS)}"}), 400

    db = SessionLocal()
    try:
        q = db.query(Flag).filter(Flag.id == flag_id)
        q = _tenant_filter(q)
        flag = q.first()
        if not flag:
            return jsonify({"error": f"Flag {flag_id} not found"}), 404

        flag.mod_status   = "dismissed" if action == "dismiss" else "actioned"
        flag.mod_action   = action
        flag.mod_note     = note
        flag.moderated_at = datetime.now(timezone.utc)
        flag.moderated_by = admin

        result_msg = f"Flag {flag_id} marked as '{action}'."

        creds = _get_creds(db)
        token = creds.page_access_token if creds else ""
        page_id = creds.page_id if creds else ""

        if action in ("warn", "block"):
            _record_user_action(db, flag.author, flag.platform or flag.source, action,
                note or f"{action.capitalize()} for {flag.label}", flag.id, admin,
                datetime.now(timezone.utc) + timedelta(days=30) if action == "warn" else None)
            if action == "warn":
                escalation = _check_auto_escalation(db, flag.author, flag.platform or flag.source, admin)
                if escalation:
                    result_msg += f" {escalation}"

        if action == "delete":
            _record_user_action(db, flag.author, flag.platform or flag.source, "delete",
                note or f"Deleted comment for {flag.label}", flag.id, admin, None)
            if flag.comment_id:
                api_result = delete_comment(flag.comment_id, token)
                if api_result:
                    result_msg += " Comment deleted from Meta platform."
                else:
                    result_msg += " Deletion recorded locally."

        db.commit()
        return jsonify({"success": True, "message": result_msg, "flag": flag.to_dict()}), 200

    except Exception as exc:
        db.rollback()
        logger.exception("Moderation action failed: %s", exc)
        return jsonify({"error": "Internal error"}), 500
    finally:
        db.close()


# ── Bulk moderation ────────────────────────────────────────────────────────────

@moderation_bp.route("/bulk", methods=["POST"])
@require_auth
@require_admin
def bulk_action():
    data     = request.get_json(silent=True) or {}
    flag_ids = data.get("flag_ids", [])
    action   = (data.get("action") or "").lower()
    note     = data.get("note", "")
    admin    = g.current_user.username

    if not flag_ids or not isinstance(flag_ids, list):
        return jsonify({"error": "'flag_ids' must be a non-empty list"}), 400
    if action not in VALID_ACTIONS:
        return jsonify({"error": f"'action' must be one of {sorted(VALID_ACTIONS)}"}), 400

    db = SessionLocal()
    try:
        q = db.query(Flag).filter(Flag.id.in_(flag_ids))
        q = _tenant_filter(q)
        flags = q.all()
        processed = []
        for flag in flags:
            flag.mod_status   = "dismissed" if action == "dismiss" else "actioned"
            flag.mod_action   = action
            flag.mod_note     = note
            flag.moderated_at = datetime.now(timezone.utc)
            flag.moderated_by = admin
            if action == "warn":
                _record_user_action(db, flag.author, flag.platform or flag.source, "warn",
                    note or f"Flagged for {flag.label}", flag.id, admin,
                    datetime.now(timezone.utc) + timedelta(days=30))
            processed.append(flag.id)

        db.commit()
        return jsonify({"success": True, "message": f"Action '{action}' applied to {len(processed)} flags.", "processed": processed}), 200
    except Exception as exc:
        db.rollback()
        return jsonify({"error": "Internal error"}), 500
    finally:
        db.close()


# ── Export flagged content as CSV ──────────────────────────────────────────────

@moderation_bp.route("/export", methods=["GET"])
@require_auth
@require_admin
def export_csv():
    label_filter  = request.args.get("label")
    status_filter = request.args.get("status")

    db = SessionLocal()
    try:
        q = _tenant_filter(db.query(Flag))
        if label_filter and label_filter != "all":
            q = q.filter(Flag.label == label_filter)
        if status_filter and status_filter != "all":
            q = q.filter(Flag.mod_status == status_filter)

        flags = q.order_by(Flag.created_at.desc()).limit(10000).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Text", "Label", "Confidence", "Severity", "Platform", "Author", "Status", "Action", "Created"])
        for f in flags:
            writer.writerow([f.id, f.text, f.label, f.confidence, f.severity,
                f.platform, f.author, f.mod_status, f.mod_action,
                f.created_at.isoformat() if f.created_at else ""])

        csv_data = output.getvalue()
        output.close()
        return Response(csv_data, mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=cyberguard_flags_export.csv"}), 200
    finally:
        db.close()


# ── User activity stats ────────────────────────────────────────────────────────

@moderation_bp.route("/user-activity", methods=["GET"])
@require_auth
@require_role("super_admin", "admin", "manager")
def user_activity():
    db = SessionLocal()
    try:
        q = _tenant_filter(
            db.query(Flag.author, func.count(Flag.id).label("flag_count"))
            .filter(Flag.is_harmful == True, Flag.author != "anonymous")
        )
        top_users = q.group_by(Flag.author).order_by(func.count(Flag.id).desc()).limit(10).all()

        bp_q = _tenant_filter(
            db.query(Flag.platform, func.count(Flag.id).label("count"))
            .filter(Flag.is_harmful == True)
        )
        by_platform = bp_q.group_by(Flag.platform).all()

        sev_q = _tenant_filter(
            db.query(Flag.severity, func.count(Flag.id).label("count"))
            .filter(Flag.is_harmful == True)
        )
        by_severity = sev_q.group_by(Flag.severity).all()

        return jsonify({
            "top_users": [{"author": u, "count": c} for u, c in top_users],
            "by_platform": {p or "unknown": c for p, c in by_platform},
            "by_severity": {s: c for s, c in by_severity},
        }), 200
    finally:
        db.close()


# ── List moderated users ───────────────────────────────────────────────────────

@moderation_bp.route("/users", methods=["GET"])
@require_auth
def list_moderated_users():
    action_filter = request.args.get("action")
    active_only   = request.args.get("active", "true").lower() == "true"
    page          = int(request.args.get("page", 1))
    per_page      = min(int(request.args.get("per_page", 20)), 100)

    db = SessionLocal()
    try:
        q = _tenant_filter(db.query(ModeratedUser), ModeratedUser)
        if action_filter:
            q = q.filter(ModeratedUser.action == action_filter)
        if active_only:
            q = q.filter(ModeratedUser.is_active == True)
        total = q.count()
        users = q.order_by(ModeratedUser.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"total": total, "page": page, "per_page": per_page, "users": [u.to_dict() for u in users]}), 200
    finally:
        db.close()


# ── Lift a moderation action ───────────────────────────────────────────────────

@moderation_bp.route("/users/<int:user_id>/lift", methods=["POST"])
@require_auth
@require_admin
def lift_action(user_id: int):
    db = SessionLocal()
    try:
        q = _tenant_filter(db.query(ModeratedUser).filter(ModeratedUser.id == user_id), ModeratedUser)
        user = q.first()
        if not user:
            return jsonify({"error": f"Record {user_id} not found"}), 404

        user.is_active = False
        db.commit()
        return jsonify({"success": True, "user": user.to_dict()}), 200
    except Exception as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()


# ── Pending queue ──────────────────────────────────────────────────────────────

@moderation_bp.route("/pending", methods=["GET"])
@require_auth
@require_role("super_admin", "admin", "manager")
def pending_flags():
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)

    db = SessionLocal()
    try:
        q = _tenant_filter(
            db.query(Flag).filter(Flag.mod_status == "pending", Flag.is_harmful == True)
        )
        total = q.count()
        flags = q.order_by(Flag.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"total": total, "page": page, "per_page": per_page, "flags": [f.to_dict() for f in flags]}), 200
    finally:
        db.close()


# ── Internal helpers ───────────────────────────────────────────────────────────

def _record_user_action(db, username, platform, action, reason, flag_id, actioned_by, expires_at):
    existing = db.query(ModeratedUser).filter(
        ModeratedUser.username == username, ModeratedUser.platform == platform,
        ModeratedUser.action == action, ModeratedUser.is_active == True).first()
    if existing:
        return
    db.add(ModeratedUser(
        tenant_id=g.current_user.tenant_id,
        username=username, platform=platform or "unknown", action=action,
        reason=reason, flag_id=flag_id, actioned_by=actioned_by,
        expires_at=expires_at, is_active=True))


def _check_auto_escalation(db, username, platform, admin):
    warn_count = db.query(ModeratedUser).filter(
        ModeratedUser.username == username, ModeratedUser.platform == platform,
        ModeratedUser.action == "warn", ModeratedUser.is_active == True).count()

    if warn_count >= BLOCK_THRESHOLD:
        already_blocked = db.query(ModeratedUser).filter(
            ModeratedUser.username == username, ModeratedUser.platform == platform,
            ModeratedUser.action == "block", ModeratedUser.is_active == True).first()
        if not already_blocked:
            _record_user_action(db, username, platform, "block",
                f"Auto-blocked after {warn_count} warnings", 0, admin, None)
            return f"AUTO-BLOCKED: @{username} has {warn_count} warnings and is now permanently blocked."
        else:
            return f"@{username} is already blocked."
    return ""

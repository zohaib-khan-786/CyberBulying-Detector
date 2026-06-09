"""
Dashboard API — tenant-scoped.
GET /api/dashboard/stats       — aggregate statistics
GET /api/dashboard/recent      — recent flagged activity feed
GET /api/dashboard/timeseries  — flags-over-time for the chart
"""

from __future__ import annotations

import time
import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from models.database import Flag, SessionLocal
from middleware.auth import require_auth, require_role

dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)


def _tenant_filter(q):
    """Scope query to current user's tenant."""
    if g.current_user.tenant_id:
        return q.filter(Flag.tenant_id == g.current_user.tenant_id)
    return q


@dashboard_bp.route("/stats", methods=["GET"])
@require_auth
@require_role("super_admin", "admin", "manager")
def stats():
    db = SessionLocal()
    try:
        base = db.query(Flag).filter(Flag.is_harmful == True)
        base = _tenant_filter(base)

        total = base.count()
        pending = base.filter(Flag.mod_status == "pending").count()

        label_q = db.query(Flag.label, func.count()).filter(Flag.is_harmful == True)
        label_q = _tenant_filter(label_q)
        label_rows = label_q.group_by(Flag.label).all()

        severity_q = db.query(Flag.severity, func.count()).filter(Flag.is_harmful == True)
        severity_q = _tenant_filter(severity_q)
        severity_rows = severity_q.group_by(Flag.severity).all()

        source_q = db.query(Flag.source, func.count()).filter(Flag.is_harmful == True)
        source_q = _tenant_filter(source_q)
        source_rows = source_q.group_by(Flag.source).all()

        return jsonify({
            "total_flagged":         total,
            "pending_moderation":    pending,
            "label_distribution":    {r[0]: r[1] for r in label_rows},
            "severity_distribution": {r[0]: r[1] for r in severity_rows},
            "source_distribution":   {r[0]: r[1] for r in source_rows},
            "last_updated":          int(time.time()),
        }), 200
    finally:
        db.close()


@dashboard_bp.route("/recent", methods=["GET"])
@require_auth
@require_role("super_admin", "admin", "manager")
def recent():
    limit = min(int(request.args.get("limit", 10)), 50)
    db = SessionLocal()
    try:
        q = db.query(Flag).filter(Flag.is_harmful == True)
        q = _tenant_filter(q)
        flags = q.order_by(Flag.created_at.desc()).limit(limit).all()
        return jsonify({"items": [f.to_dict() for f in flags]}), 200
    finally:
        db.close()


@dashboard_bp.route("/timeseries", methods=["GET"])
@require_auth
@require_role("super_admin", "admin", "manager")
def timeseries():
    hours = min(int(request.args.get("hours", 24)), 168)
    since = datetime.utcnow() - timedelta(hours=hours)

    db = SessionLocal()
    try:
        q = db.query(Flag).filter(Flag.is_harmful == True, Flag.created_at >= since)
        q = _tenant_filter(q)
        rows = q.order_by(Flag.created_at.asc()).all()

        buckets: dict[str, dict] = {}
        for flag in rows:
            hour_key = flag.created_at.strftime("%Y-%m-%dT%H:00")
            if hour_key not in buckets:
                buckets[hour_key] = {"hour": hour_key, "total": 0, "by_label": {}}
            buckets[hour_key]["total"] += 1
            lbl = flag.label
            buckets[hour_key]["by_label"][lbl] = buckets[hour_key]["by_label"].get(lbl, 0) + 1

        return jsonify({"hours": hours, "points": list(buckets.values())}), 200
    finally:
        db.close()

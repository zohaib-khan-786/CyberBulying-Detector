"""
Dashboard API
GET /api/dashboard/stats     — aggregate statistics + hourly timeseries
GET /api/dashboard/recent    — recent flagged activity feed
GET /api/dashboard/timeseries — flags-over-time for the chart
"""

from __future__ import annotations

import time
import logging
from collections import Counter
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from models.database import Flag, SessionLocal
from middleware.auth import require_auth

dashboard_bp = Blueprint("dashboard", __name__)
logger       = logging.getLogger(__name__)


@dashboard_bp.route("/stats", methods=["GET"])
@require_auth
def stats():
    db = SessionLocal()
    try:
        total = db.query(Flag).filter(Flag.is_harmful == True).count()
        pending = db.query(Flag).filter(
            Flag.is_harmful == True, Flag.mod_status == "pending"
        ).count()

        label_rows    = db.query(Flag.label,    func.count()).filter(Flag.is_harmful == True).group_by(Flag.label).all()
        severity_rows = db.query(Flag.severity, func.count()).filter(Flag.is_harmful == True).group_by(Flag.severity).all()
        source_rows   = db.query(Flag.source,   func.count()).filter(Flag.is_harmful == True).group_by(Flag.source).all()

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
def recent():
    limit = min(int(request.args.get("limit", 10)), 50)
    db = SessionLocal()
    try:
        flags = (
            db.query(Flag)
            .filter(Flag.is_harmful == True)
            .order_by(Flag.created_at.desc())
            .limit(limit)
            .all()
        )
        return jsonify({"items": [f.to_dict() for f in flags]}), 200
    finally:
        db.close()


@dashboard_bp.route("/timeseries", methods=["GET"])
@require_auth
def timeseries():
    """
    Returns hourly flag counts for the last N hours (default 24).
    Powers the time-series chart on the dashboard.
    Response shape: [ { "hour": "2024-05-14T10:00", "total": 5, "by_label": {...} }, ... ]
    """
    hours = min(int(request.args.get("hours", 24)), 168)  # cap at 1 week
    since = datetime.utcnow() - timedelta(hours=hours)

    db = SessionLocal()
    try:
        rows = (
            db.query(Flag)
            .filter(Flag.is_harmful == True, Flag.created_at >= since)
            .order_by(Flag.created_at.asc())
            .all()
        )

        # Bucket into hours
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

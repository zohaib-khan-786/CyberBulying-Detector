"""
JWT authentication middleware for Flask.

Usage
-----
from middleware.auth import require_auth, require_admin, require_role

@app.route("/protected")
@require_auth
def protected_route():
    user = g.current_user
    return jsonify({"user": user.to_dict()})
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, g, current_app

from models.database import SessionLocal
from models.user import User

logger = logging.getLogger(__name__)

JWT_SECRET    = os.getenv("JWT_SECRET_KEY", "change-me-in-production-32char!")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_H  = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
JWT_REFRESH_D = int(os.getenv("JWT_REFRESH_DAYS", "30"))


# ── Token helpers ─────────────────────────────────────────────────────────────

def generate_access_token(user: User) -> str:
    """Create a short-lived access token."""
    payload = {
        "sub":       str(user.id),
        "role":      user.role,
        "tenant_id": user.tenant_id,
        "exp":       datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_H),
        "iat":       datetime.now(timezone.utc),
        "type":      "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_refresh_token(user: User) -> str:
    """Create a long-lived refresh token."""
    payload = {
        "sub":       str(user.id),
        "role":      user.role,
        "tenant_id": user.tenant_id,
        "exp":       datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_D),
        "iat":       datetime.now(timezone.utc),
        "type":      "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT. Returns payload dict or None on failure."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired.")
        return None
    except jwt.InvalidTokenError as exc:
        logger.debug("Invalid token: %s", exc)
        return None


# ── Decorators ────────────────────────────────────────────────────────────────

def require_auth(f):
    """Decorator: valid JWT required. Injects g.current_user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401

        token = auth_header[7:]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        if payload.get("type") != "access":
            return jsonify({"error": "Expected an access token"}), 401

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(payload["sub"])).first()
            if not user or not user.is_active:
                return jsonify({"error": "User not found or deactivated"}), 401
            g.current_user = user
            g.db = db
        except Exception:
            db.close()
            return jsonify({"error": "Authentication failed"}), 500

        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    """Decorator: super_admin or admin role required. Must be stacked after @require_auth."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user or user.role not in ("super_admin", "admin"):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated


def require_role(*roles: str):
    """Decorator factory: require one of the specified roles.
    Must be stacked after @require_auth.

    Usage:
        @require_role("admin", "manager")
        def my_view(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user or user.role not in roles:
                rlist = ", ".join(roles)
                return jsonify({"error": f"Requires one of these roles: {rlist}"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

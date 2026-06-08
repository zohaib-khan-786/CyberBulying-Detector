"""
Auth endpoints
POST /api/auth/register  — create a new user account
POST /api/auth/login     — obtain JWT access + refresh tokens
GET  /api/auth/me        — current user profile (protected)
POST /api/auth/refresh   — refresh an access token
GET  /api/auth/users     — list all users (admin only)
"""

from __future__ import annotations

import logging

from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError

from models.database import SessionLocal
from models.user import User
from middleware.auth import (
    require_auth,
    require_admin,
    generate_access_token,
    generate_refresh_token,
    decode_token,
)

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Validate
    for validator, value in [
        (User.validate_username, username),
        (User.validate_email,    email),
        (User.validate_password, password),
    ]:
        err = validator(value)
        if err:
            return jsonify({"error": err}), 400

    db = SessionLocal()
    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New user registered: @%s", username)
        return jsonify({"user": user.to_dict()}), 201
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as exc:
        db.rollback()
        logger.exception("Registration failed: %s", exc)
        return jsonify({"error": "Registration failed"}), 500
    finally:
        db.close()


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        access_token  = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        logger.info("User @%s logged in.", username)
        return jsonify({
            "user":          user.to_dict(),
            "access_token":  access_token,
            "refresh_token": refresh_token,
        }), 200
    finally:
        db.close()


# ── Current user ──────────────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    user = g.current_user
    return jsonify({"user": user.to_dict()}), 200


# ── Refresh ───────────────────────────────────────────────────────────────────

@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json(silent=True) or {}
    token = data.get("refresh_token") or ""

    if not token:
        return jsonify({"error": "refresh_token is required"}), 400

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.is_active:
            return jsonify({"error": "User not found or deactivated"}), 401

        new_access = generate_access_token(user)
        return jsonify({"access_token": new_access}), 200
    finally:
        db.close()


# ── List users (admin only) ──────────────────────────────────────────────────

@auth_bp.route("/users", methods=["GET"])
@require_auth
@require_admin
def list_users():
    db = SessionLocal()
    try:
        page     = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)

        total = db.query(User).count()
        users = (
            db.query(User)
            .order_by(User.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "total":    total,
            "page":     page,
            "per_page": per_page,
            "users":    [u.to_dict() for u in users],
        }), 200
    finally:
        db.close()


# ── Update user role (admin only) ────────────────────────────────────────────

@auth_bp.route("/users/<int:user_id>/role", methods=["PATCH"])
@require_auth
@require_admin
def update_role(user_id: int):
    data = request.get_json(silent=True) or {}
    new_role = (data.get("role") or "").strip()

    if new_role not in ("admin", "user"):
        return jsonify({"error": "Role must be 'admin' or 'user'"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.role = new_role
        db.commit()
        logger.info("User @%s role changed to '%s' by admin", user.username, new_role)
        return jsonify({"user": user.to_dict()}), 200
    finally:
        db.close()


# ── Deactivate user (admin only) ─────────────────────────────────────────────

@auth_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@require_auth
@require_admin
def deactivate_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_active = False
        db.commit()
        logger.info("User @%s deactivated by admin", user.username)
        return jsonify({"user": user.to_dict()}), 200
    finally:
        db.close()


# ── Activate user (admin only) ───────────────────────────────────────────────

@auth_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@require_auth
@require_admin
def activate_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_active = True
        db.commit()
        logger.info("User @%s activated by admin", user.username)
        return jsonify({"user": user.to_dict()}), 200
    finally:
        db.close()

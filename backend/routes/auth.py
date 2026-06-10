"""
Auth endpoints
POST /api/auth/register          — create a new tenant + admin account
POST /api/auth/login             — obtain JWT access + refresh tokens
GET  /api/auth/me                — current user profile (protected)
POST /api/auth/refresh           — refresh an access token
GET  /api/auth/users             — list users in tenant (admin only)
POST /api/auth/users             — create a manager user (admin only)
PATCH /api/auth/users/<id>/role  — change user role (admin only)
POST /api/auth/users/<id>/deactivate — deactivate user (admin only)
POST /api/auth/users/<id>/activate   — activate user (admin only)
"""

from __future__ import annotations

import logging

from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError

from models.database import SessionLocal, Tenant
from models.user import User, VALID_ROLES
from utils.email import send_password_reset_email, is_smtp_configured
from middleware.auth import (
    require_auth,
    require_admin,
    generate_access_token,
    generate_refresh_token,
    decode_token,
)

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


# ── Register (creates a new tenant) ───────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    tenant_name = (data.get("tenant_name") or username).strip()

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
        tenant = Tenant(name=tenant_name)
        db.add(tenant)
        db.flush()

        user = User(username=username, email=email, role="admin", tenant_id=tenant.id)
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New tenant '%s' + admin '@%s' registered.", tenant_name, username)
        return jsonify({"user": user.to_dict(), "tenant_name": tenant.name}), 201
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

        logger.info("User @%s logged in (role=%s, tenant=%s).", username, user.role, user.tenant_id)
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


# ── Forgot password ───────────────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({"error": "No account found with that email"}), 404

        token = user.generate_reset_token()
        db.commit()
        logger.info("Reset token generated for %s", email)

        sent = send_password_reset_email(email, token)

        if sent:
            return jsonify({
                "message": "Password reset link has been sent to your email.",
            }), 200

        if is_smtp_configured():
            logger.error("SMTP is configured but email delivery failed for %s", email)
            return jsonify({"error": "Failed to send email. Please contact support."}), 500

        return jsonify({
            "message": "Reset code generated",
            "reset_token": token,
            "note": "SMTP not configured. Save this code to reset your password.",
        }), 200
    except Exception as exc:
        db.rollback()
        logger.exception("Forgot password failed: %s", exc)
        return jsonify({"error": "Failed to process request"}), 500
    finally:
        db.close()


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"error": "Token and new_password are required"}), 400

    err = User.validate_password(new_password)
    if err:
        return jsonify({"error": err}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.reset_token == token).first()
        if not user or not user.verify_reset_token(token):
            return jsonify({"error": "Invalid or expired reset token"}), 401

        user.set_password(new_password)
        user.clear_reset_token()
        db.commit()
        logger.info("Password reset for @%s", user.username)
        return jsonify({"message": "Password reset successfully"}), 200
    except Exception as exc:
        db.rollback()
        logger.exception("Reset password failed: %s", exc)
        return jsonify({"error": "Failed to reset password"}), 500
    finally:
        db.close()


# ── List users (tenant-scoped) ────────────────────────────────────────────────

@auth_bp.route("/users", methods=["GET"])
@require_auth
@require_admin
def list_users():
    db = g.get("db") or SessionLocal()
    close = "db" not in g
    try:
        page     = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)

        q = db.query(User)
        if g.current_user.role != "super_admin":
            q = q.filter(User.tenant_id == g.current_user.tenant_id)

        total = q.count()
        users = (
            q.order_by(User.created_at.desc())
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
        if close:
            db.close()


# ── Create manager user (admin only) ──────────────────────────────────────────

@auth_bp.route("/users", methods=["POST"])
@require_auth
@require_admin
def create_user():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role     = (data.get("role") or "manager").strip()

    if role not in ("manager", "admin"):
        return jsonify({"error": "Role must be 'manager' or 'admin'"}), 400

    # Only super_admin can create other admins
    if role == "admin" and g.current_user.role != "super_admin":
        return jsonify({"error": "Only super_admin can create admin users"}), 403

    for validator, value in [
        (User.validate_username, username),
        (User.validate_email,    email),
        (User.validate_password, password),
    ]:
        err = validator(value)
        if err:
            return jsonify({"error": err}), 400

    db = g.get("db") or SessionLocal()
    close = "db" not in g
    try:
        if role == "admin" and g.current_user.role == "super_admin":
            # Creating an admin → give them their own tenant
            tenant_name = data.get("tenant_name") or f"{username}-workspace"
            tenant = Tenant(name=tenant_name)
            db.add(tenant)
            db.flush()
            user = User(username=username, email=email, role="admin", tenant_id=tenant.id)
            user.set_password(password)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("New tenant '%s' + admin '@%s' created by super_admin.", tenant_name, username)
            return jsonify({"user": user.to_dict(), "tenant_name": tenant.name}), 201
        else:
            # Creating a manager → assign to a specific tenant
            target_tenant_id = data.get("tenant_id") or g.current_user.tenant_id

            # Super_admin must specify a tenant_id for managers
            if g.current_user.role == "super_admin" and not data.get("tenant_id"):
                return jsonify({"error": "super_admin must specify tenant_id when creating a manager"}), 400

            # Verify the target tenant exists
            tenant = db.query(Tenant).filter(Tenant.id == target_tenant_id).first()
            if not tenant:
                return jsonify({"error": "Tenant not found"}), 404

            # Non-super-admin can only create managers in their own tenant
            if g.current_user.role != "super_admin" and target_tenant_id != g.current_user.tenant_id:
                return jsonify({"error": "You can only create users in your own tenant"}), 403

            user = User(username=username, email=email, role="manager", tenant_id=target_tenant_id)
            user.set_password(password)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Manager @%s created in tenant %s by @%s.", username, target_tenant_id, g.current_user.username)
            return jsonify({"user": user.to_dict()}), 201
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create user: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        if close:
            db.close()


# ── Update user role ──────────────────────────────────────────────────────────

@auth_bp.route("/users/<int:user_id>/role", methods=["PATCH"])
@require_auth
@require_admin
def update_role(user_id: int):
    data = request.get_json(silent=True) or {}
    new_role = (data.get("role") or "").strip()

    if new_role not in VALID_ROLES:
        return jsonify({"error": f"Role must be one of {sorted(VALID_ROLES)}"}), 400

    db = g.get("db") or SessionLocal()
    close = "db" not in g
    try:
        q = db.query(User).filter(User.id == user_id)
        if g.current_user.role != "super_admin":
            q = q.filter(User.tenant_id == g.current_user.tenant_id)

        user = q.first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.role = new_role
        db.commit()
        logger.info("User @%s role changed to '%s' by @%s", user.username, new_role, g.current_user.username)
        return jsonify({"user": user.to_dict()}), 200
    finally:
        if close:
            db.close()


# ── Deactivate user ───────────────────────────────────────────────────────────

@auth_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@require_auth
@require_admin
def deactivate_user(user_id: int):
    db = g.get("db") or SessionLocal()
    close = "db" not in g
    try:
        q = db.query(User).filter(User.id == user_id)
        if g.current_user.role != "super_admin":
            q = q.filter(User.tenant_id == g.current_user.tenant_id)

        user = q.first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_active = False
        db.commit()
        logger.info("User @%s deactivated by @%s", user.username, g.current_user.username)
        return jsonify({"user": user.to_dict()}), 200
    finally:
        if close:
            db.close()


# ── Activate user ─────────────────────────────────────────────────────────────

@auth_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@require_auth
@require_admin
def activate_user(user_id: int):
    db = g.get("db") or SessionLocal()
    close = "db" not in g
    try:
        q = db.query(User).filter(User.id == user_id)
        if g.current_user.role != "super_admin":
            q = q.filter(User.tenant_id == g.current_user.tenant_id)

        user = q.first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_active = True
        db.commit()
        logger.info("User @%s activated by @%s", user.username, g.current_user.username)
        return jsonify({"user": user.to_dict()}), 200
    finally:
        if close:
            db.close()

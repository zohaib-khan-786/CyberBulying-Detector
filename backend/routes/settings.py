"""
Settings endpoints — per-tenant Meta API credentials management.

GET  /api/settings/meta       — get current Meta credentials
PUT  /api/settings/meta       — update Meta credentials
POST /api/settings/meta/test  — test Meta credentials by calling /me
POST /api/settings/meta/refresh — refresh page access token
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, request, jsonify, g
import requests

from models.database import MetaCredentials, SessionLocal
from middleware.auth import require_auth, require_admin
from models.user import User

settings_bp = Blueprint("settings", __name__)
logger = logging.getLogger(__name__)


def _get_creds(db) -> MetaCredentials | None:
    """Get the active Meta credentials for the current user's tenant."""
    tenant_id = g.current_user.tenant_id
    if not tenant_id:
        return None
    return db.query(MetaCredentials).filter(
        MetaCredentials.tenant_id == tenant_id,
        MetaCredentials.is_active == True,
    ).first()


def _ensure_creds(db) -> MetaCredentials:
    """Get or create Meta credentials for the current tenant."""
    creds = _get_creds(db)
    if creds:
        return creds
    creds = MetaCredentials(tenant_id=g.current_user.tenant_id)
    db.add(creds)
    db.commit()
    db.refresh(creds)
    return creds


# ── GET current Meta credentials ──────────────────────────────────────────────

@settings_bp.route("/meta", methods=["GET"])
@require_auth
@require_admin
def get_meta_credentials():
    db = SessionLocal()
    try:
        creds = _get_creds(db)
        if not creds:
            return jsonify({
                "configured": False,
                "credentials": None,
            }), 200
        return jsonify({
            "configured": True,
            "credentials": creds.to_dict(),
        }), 200
    finally:
        db.close()


# ── PUT update Meta credentials ───────────────────────────────────────────────

@settings_bp.route("/meta", methods=["PUT"])
@require_auth
@require_admin
def update_meta_credentials():
    data = request.get_json(silent=True) or {}

    db = SessionLocal()
    try:
        creds = _ensure_creds(db)

        if "page_id" in data:
            new_page_id = str(data["page_id"]).strip()
            # Enforce: one page can only belong to one active tenant
            existing = db.query(MetaCredentials).filter(
                MetaCredentials.page_id == new_page_id,
                MetaCredentials.is_active == True,
                MetaCredentials.tenant_id != g.current_user.tenant_id,
            ).first()
            if existing:
                return jsonify({
                    "error": f"Page '{new_page_id}' is already registered to another tenant. "
                              "A page can only be owned by one tenant."
                }), 409
            creds.page_id = new_page_id

        if "app_id" in data:
            creds.app_id = data["app_id"]
        if "app_secret" in data:
            creds.app_secret = data["app_secret"]
        if "page_access_token" in data:
            creds.page_access_token = data["page_access_token"]
        if "webhook_verify_token" in data:
            creds.webhook_verify_token = data["webhook_verify_token"]

        db.commit()
        db.refresh(creds)
        logger.info("Meta credentials updated for tenant %d", g.current_user.tenant_id)
        return jsonify({
            "success": True,
            "credentials": creds.to_dict(),
        }), 200
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update Meta credentials: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()


# ── POST test Meta credentials ────────────────────────────────────────────────

@settings_bp.route("/meta/test", methods=["POST"])
@require_auth
@require_admin
def test_meta_credentials():
    db = SessionLocal()
    try:
        creds = _get_creds(db)
        if not creds or not creds.page_access_token:
            return jsonify({"error": "No Meta credentials configured. Set them first."}), 400

        token = creds.page_access_token
        results = {}

        # Test /me
        try:
            resp = requests.get(
                "https://graph.facebook.com/v25.0/me",
                params={"access_token": token, "fields": "id,name"},
                timeout=10
            )
            data = resp.json()
            if "error" in data:
                results["token_valid"] = {"status": "FAIL", "error": data["error"].get("message")}
            else:
                results["token_valid"] = {"status": "PASS", "name": data.get("name"), "id": data.get("id")}
        except Exception as e:
            results["token_valid"] = {"status": "ERROR", "error": str(e)}

        # Test page access
        page_id = creds.page_id
        if page_id:
            try:
                resp = requests.get(
                    f"https://graph.facebook.com/v25.0/{page_id}",
                    params={"access_token": token, "fields": "name,id"},
                    timeout=10
                )
                data = resp.json()
                if "error" in data:
                    results["page_access"] = {"status": "FAIL", "error": data["error"].get("message")}
                else:
                    results["page_access"] = {"status": "PASS", "name": data.get("name")}
            except Exception as e:
                results["page_access"] = {"status": "ERROR", "error": str(e)}

        # Test Instagram account
        if page_id:
            try:
                resp = requests.get(
                    f"https://graph.facebook.com/v25.0/{page_id}",
                    params={"access_token": token, "fields": "instagram_business_account"},
                    timeout=10
                )
                data = resp.json()
                ig = data.get("instagram_business_account")
                if ig:
                    results["instagram"] = {"status": "PASS", "id": ig.get("id")}
                    # Save it
                    creds.instagram_account_id = ig.get("id")
                else:
                    results["instagram"] = {"status": "SKIP", "note": "No Instagram Business Account linked to this page"}
            except Exception as e:
                results["instagram"] = {"status": "ERROR", "error": str(e)}

        db.commit()
        return jsonify({"results": results}), 200

    except Exception as exc:
        logger.exception("Meta test failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()

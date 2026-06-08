"""
Meta Graph API helper — calls Facebook/Instagram APIs to perform
actual moderation actions (delete comments, block users).

Docs: https://developers.facebook.com/docs/graph-api/overview
"""

from __future__ import annotations

import os
import logging
import requests

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v25.0"
GRAPH_API_BASE    = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _get_token() -> str:
    """Read token at runtime so .env changes take effect."""
    return os.getenv("META_PAGE_ACCESS_TOKEN", "")


def _api_call(method: str, endpoint: str, **kwargs) -> dict | None:
    """Make a Graph API call. Returns response JSON or None on failure."""
    token = _get_token()
    if not token:
        logger.warning("META_PAGE_ACCESS_TOKEN not set — API call skipped.")
        return None

    url = f"{GRAPH_API_BASE}/{endpoint}"
    params = kwargs.pop("params", {})
    params["access_token"] = token

    try:
        resp = requests.request(method, url, params=params, timeout=10, **kwargs)
        data = resp.json()

        if resp.status_code >= 400:
            error = data.get("error", {})
            logger.error("Graph API error %s %s: %s", method, endpoint, error.get("message", "unknown"))
            return None

        return data
    except Exception as exc:
        logger.error("Graph API request failed: %s", exc)
        return None


# ── Delete a comment ──────────────────────────────────────────────────────────

def delete_comment(comment_id: str) -> bool:
    """
    Delete a comment on Facebook/Instagram.
    comment_id: The Graph API comment ID (not our Flag.id).

    Facebook:  DELETE /{comment_id}
    Instagram: DELETE /{comment_id}  (same endpoint)
    """
    if not comment_id:
        logger.warning("delete_comment called with empty comment_id")
        return False

    result = _api_call("DELETE", comment_id)
    if result and result.get("success"):
        logger.info("Comment %s deleted via Graph API", comment_id)
        return True
    return False


# ── Block a user from a page ─────────────────────────────────────────────────

def block_user(page_id: str, user_id: str, platform: str = "facebook") -> bool:
    """
    Block a user from interacting with a Facebook Page.
    Note: Many Page types don't support this endpoint (error_subcode 33).
    Returns False to indicate the action was recorded locally only.

    page_id:  Your Facebook Page ID
    user_id:  The user's Facebook/Instagram user ID
    platform: "facebook" or "instagram"
    """
    if not page_id or not user_id:
        logger.warning("block_user called with missing page_id or user_id")
        return False

    if platform == "instagram":
        logger.info("Instagram block — no Graph API block endpoint available.")
        return False

    # Most Page types don't support blocked_users endpoint (error_subcode 33)
    # Record locally instead
    logger.info("Block recorded locally for user %s on page %s (Graph API block not supported for this Page type)", user_id, page_id)
    return False


# ── Unblock a user from a page ───────────────────────────────────────────────

def unblock_user(page_id: str, user_id: str) -> bool:
    """
    Unblock a user from a Facebook Page.
    Note: Most Page types don't support this endpoint. Records locally.
    """
    if not page_id or not user_id:
        return False

    logger.info("Unblock recorded locally for user %s on page %s (Graph API unblock not supported for this Page type)", user_id, page_id)
    return False


# ── Hide a comment (soft delete) ─────────────────────────────────────────────

def hide_comment(comment_id: str) -> bool:
    """
    Hide a comment (only visible to comment author).
    POST /{comment_id}
    Body: is_hidden=true
    """
    if not comment_id:
        return False

    result = _api_call("POST", comment_id, params={"is_hidden": "true"})
    if result:
        logger.info("Comment %s hidden via Graph API", comment_id)
        return True
    return False


# ── Get comment details ──────────────────────────────────────────────────────

def get_comment_info(comment_id: str) -> dict | None:
    """Fetch comment details from Graph API."""
    if not comment_id:
        return None
    return _api_call("GET", comment_id, params={"fields": "id,message,from,created_time"})

"""
Meta Graph API helper — calls Facebook/Instagram APIs to perform
actual moderation actions (delete comments, block users).
All functions accept an explicit access_token for multi-tenant support.
"""

from __future__ import annotations

import logging
import requests

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v25.0"
GRAPH_API_BASE    = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _api_call(method: str, endpoint: str, token: str, **kwargs) -> dict | None:
    """Make a Graph API call. Returns response JSON or None on failure."""
    if not token:
        logger.warning("Access token not provided — API call skipped.")
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


def delete_comment(comment_id: str, token: str) -> bool:
    """Delete a comment on Facebook/Instagram."""
    if not comment_id:
        logger.warning("delete_comment called with empty comment_id")
        return False

    result = _api_call("DELETE", comment_id, token)
    if result and result.get("success"):
        logger.info("Comment %s deleted via Graph API", comment_id)
        return True
    return False


def hide_comment(comment_id: str, token: str) -> bool:
    """Hide a comment (only visible to comment author)."""
    if not comment_id:
        return False

    result = _api_call("POST", comment_id, token, params={"is_hidden": "true"})
    if result:
        logger.info("Comment %s hidden via Graph API", comment_id)
        return True
    return False


def get_comment_info(comment_id: str, token: str) -> dict | None:
    """Fetch comment details from Graph API."""
    if not comment_id:
        return None
    return _api_call("GET", comment_id, token, params={"fields": "id,message,from,created_time"})

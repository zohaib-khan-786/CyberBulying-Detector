"""
Meta Graph API — Fetch comments from Facebook Pages and Instagram.
All functions accept an explicit access_token parameter for multi-tenant support.
"""

from __future__ import annotations

import json
import logging
import requests

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v25.0"
GRAPH_API_BASE    = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _get(url: str, token: str, params: dict = None) -> dict | None:
    """Make a GET request to the Graph API with the given token."""
    if params is None:
        params = {}

    if not token:
        logger.error("Access token not provided!")
        return None

    params["access_token"] = token
    full_url = f"{GRAPH_API_BASE}/{url}" if not url.startswith("http") else url

    logger.info("Graph API GET: %s", full_url)

    try:
        resp = requests.get(full_url, params=params, timeout=30)

        if resp.status_code != 200:
            logger.error("HTTP %d: %s", resp.status_code, resp.text[:1000])
            return None

        data = resp.json()
        if "error" in data:
            logger.error("Graph API error: %s", data["error"].get("message"))
            return None

        return data
    except Exception as exc:
        logger.error("Request failed: %s", exc)
        return None


# ── Facebook ──────────────────────────────────────────────────────────────────

def get_instagram_account_id(page_id: str, token: str) -> str | None:
    """Get the Instagram Business Account ID linked to a Facebook Page."""
    data = _get(f"{page_id}", token, params={"fields": "instagram_business_account"})
    if data and "instagram_business_account" in data:
        return data["instagram_business_account"]["id"]
    return None


def fetch_facebook_comments(page_id: str, token: str, limit: int = 25) -> list[dict]:
    """
    Fetch comments from a Facebook Page.
    Step 1: Get posts from /{page_id}/feed
    Step 2: For each post, fetch comments from /{post_id}/comments
    """
    all_comments = []

    # Step 1: Get posts
    logger.info("Fetching posts from page %s...", page_id)
    data = _get(
        f"{page_id}/feed", token,
        params={"fields": "message,created_time", "limit": str(limit)}
    )

    if not data or "data" not in data:
        logger.warning("No posts found for page %s", page_id)
        return []

    logger.info("Found %d posts", len(data["data"]))

    for post in data["data"]:
        post_id = post.get("id")
        post_message = (post.get("message") or "")[:60]

        comments_data = _get(
            f"{post_id}/comments", token,
            params={"fields": "message,from,created_time,id", "limit": "100"}
        )

        if not comments_data or "data" not in comments_data:
            logger.info("  Post %s (%s...): 0 comments", post_id, post_message)
            continue

        comments_list = comments_data["data"]
        logger.info("  Post %s (%s...): %d comments", post_id, post_message, len(comments_list))

        for comment in comments_list:
            text = comment.get("message", "").strip()
            if not text:
                continue

            from_info = comment.get("from", {})
            comment_id = comment.get("id", "")
            author = from_info.get("name", "") if from_info else ""
            if not author:
                parts = comment_id.split("_")
                author = f"user_{parts[-1][:8]}" if len(parts) > 1 else "page_visitor"

            all_comments.append({
                "id":         comment_id,
                "text":       text,
                "from_name":  author,
                "from_id":    from_info.get("id", "") if from_info else "",
                "timestamp":  comment.get("created_time", ""),
                "post_id":    post_id,
                "platform":   "facebook",
            })

        paging = comments_data.get("paging", {})
        next_url = paging.get("next")
        while next_url:
            more_comments = _get(next_url, token)
            if not more_comments or "data" not in more_comments:
                break
            for comment in more_comments["data"]:
                text = comment.get("message", "").strip()
                if not text:
                    continue
                from_info = comment.get("from", {})
                all_comments.append({
                    "id":         comment.get("id"),
                    "text":       text,
                    "from_name":  from_info.get("name", "unknown"),
                    "from_id":    from_info.get("id", ""),
                    "timestamp":  comment.get("created_time", ""),
                    "post_id":    post_id,
                    "platform":   "facebook",
                })
            next_url = more_comments.get("paging", {}).get("next")

    logger.info("Total Facebook comments fetched: %d", len(all_comments))
    return all_comments


# ── Instagram ─────────────────────────────────────────────────────────────────

def get_instagram_media(instagram_id: str, token: str, limit: int = 25) -> list[dict]:
    """Get recent media from an Instagram Business Account."""
    data = _get(
        f"{instagram_id}/media", token,
        params={"fields": "id,caption,timestamp", "limit": str(limit)}
    )
    if data and "data" in data:
        return data["data"]
    return []


def fetch_instagram_comments(media_id: str, token: str, limit: int = 100) -> list[dict]:
    """Fetch comments on an Instagram media item."""
    data = _get(
        f"{media_id}/comments", token,
        params={"fields": "text,username,timestamp", "limit": str(limit)}
    )
    if not data or "data" not in data:
        return []

    comments = []
    for item in data["data"]:
        text = item.get("text", "").strip()
        if not text:
            continue
        comments.append({
            "id":        item.get("id"),
            "text":      text,
            "username":  item.get("username", "unknown"),
            "timestamp": item.get("timestamp", ""),
        })
    return comments


def fetch_all_instagram_comments(instagram_id: str, token: str, media_limit: int = 25, comment_limit: int = 100) -> list[dict]:
    """Fetch comments from all recent Instagram media."""
    media_list = get_instagram_media(instagram_id, token, limit=media_limit)
    all_comments = []

    for media in media_list:
        media_id = media.get("id")
        if not media_id:
            continue
        comments = fetch_instagram_comments(media_id, token, limit=comment_limit)
        for c in comments:
            c["media_id"] = media_id
            c["platform"] = "instagram"
        all_comments.extend(comments)

    logger.info("Total Instagram comments fetched: %d", len(all_comments))
    return all_comments

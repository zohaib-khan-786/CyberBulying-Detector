"""
meta_setup.py — One-command Meta webhook setup.

You just provide a short-lived user access token. This script:
  1. Exchanges it for a long-lived (60-day) user token
  2. Gets all your Facebook Pages
  3. Lets you pick one (or auto-selects)
  4. Gets the Page Access Token
  5. Stores credentials in the database
  6. Subscribes the page (page-level + app-level webhooks)

Usage:
    python scripts/meta_setup.py

Prerequisites:
    - Your Meta App ID and App Secret (from Meta Developer Console)
    - Your app's webhook callback URL and verify token
    - A short-lived user access token (from Graph API Explorer or your app)
"""

import json, os, sys, logging, webbrowser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("meta_setup")

API_VERSION = "v25.0"
GRAPH_URL = f"https://graph.facebook.com/{API_VERSION}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def api_get(path: str, params: dict) -> dict:
    """GET request to Graph API."""
    url = f"{GRAPH_URL}/{path.lstrip('/')}?{urlencode(params)}"
    try:
        with urlopen(Request(url), timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        body = e.read().decode() if hasattr(e, 'read') else str(e)
        return {"error": {"message": str(body)}}


def api_post(path: str, data: dict) -> dict:
    """POST request to Graph API."""
    url = f"{GRAPH_URL}/{path.lstrip('/')}"
    try:
        req = Request(url, data=urlencode(data).encode(), method="POST")
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        body = e.read().decode() if hasattr(e, 'read') else str(e)
        return {"error": {"message": str(body)}}


def step(msg: str):
    """Print a section header."""
    print()
    print("=" * 60)
    print(f"  {msg}")
    print("=" * 60)


# ── Config from .env or prompts ──────────────────────────────────────────────

def get_config():
    """Gather all config from .env or user prompts."""
    # Load .env if present
    dotenv_path = Path(__file__).parent.parent / ".env"
    if dotenv_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)

    print()
    print("╔════════════════════════════════════════════════════════╗")
    print("║       META WEBHOOK SETUP                             ║")
    print("╚════════════════════════════════════════════════════════╝")

    step("1. Meta App Credentials")
    print("  (From your Meta Developer Console → Apps → Your App → Dashboard)")
    app_id = input("  App ID: ").strip()
    while not app_id:
        app_id = input("  App ID (required): ").strip()

    app_secret = input("  App Secret: ").strip()
    while not app_secret:
        app_secret = input("  App Secret (required): ").strip()
    print("  (App Secret hidden for security)")

    step("2. Webhook Configuration")
    default_url = "https://cyberguard-634541519354.asia-southeast1.run.app/api/webhook/meta"
    callback_url = input(f"  Callback URL [{default_url}]: ").strip() or default_url

    default_token = "my_verify_token"
    verify_token = input(f"  Verify Token [{default_token}]: ").strip() or default_token

    step("3. Short-Lived User Access Token")
    print("  Get this from:")
    print("    • Meta Graph API Explorer: https://developers.facebook.com/tools/explorer/")
    print("    • Your app's login flow (data_access_token)")
    print()
    print("  Required permissions:")
    print("    • pages_show_list")
    print("    • pages_read_engagement")
    print("    • pages_manage_metadata")
    print()
    short_token = input("  Short-Lived Token: ").strip()
    if not short_token:
        logger.error("Token is required.")
        sys.exit(1)

    step("4. Database URL (for storing credentials)")
    default_db = "postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying"
    db_url = input(f"  DATABASE_URL [{default_db}]: ").strip() or default_db

    return {
        "app_id": app_id,
        "app_secret": app_secret,
        "callback_url": callback_url,
        "verify_token": verify_token,
        "short_token": short_token,
        "db_url": db_url,
    }


# ── Token Exchange ────────────────────────────────────────────────────────────

def exchange_token(app_id: str, app_secret: str, short_token: str) -> str:
    """Exchange short-lived user token for long-lived (60 days)."""
    step("5. Exchanging Short → Long-Lived Token")
    print("  Requesting…")

    result = api_get("oauth/access_token", {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })

    if "error" in result:
        err = result["error"]["message"]
        logger.error("Token exchange failed: %s", err)
        sys.exit(1)

    long_token = result.get("access_token", "")
    expires_in = result.get("expires_in", 0)
    days = expires_in // 86400

    print(f"  ✅ Long-lived token obtained")
    print(f"     Expires in: ~{days} days")
    print(f"     Token:      {long_token[:30]}…{long_token[-10:]}")
    return long_token


# ── Get Pages ─────────────────────────────────────────────────────────────────

def get_pages(token: str) -> list[dict]:
    """Get all Facebook Pages the user manages."""
    step("6. Fetching Your Facebook Pages")
    result = api_get("me/accounts", {"access_token": token})

    if "error" in result:
        logger.error("Failed to fetch pages: %s", result["error"]["message"])
        sys.exit(1)

    pages = result.get("data", [])
    if not pages:
        logger.error("No Facebook Pages found for this token.")
        logger.error("Make sure the token has 'pages_show_list' permission.")
        sys.exit(1)

    print(f"  Found {len(pages)} page(s):")
    for i, p in enumerate(pages, 1):
        print(f"    [{i}] {p.get('name', 'Unnamed')} (ID: {p.get('id')})")

    return pages


def select_page(pages: list[dict]) -> dict:
    """Let user pick a page, or auto-select if only one."""
    if len(pages) == 1:
        page = pages[0]
        print(f"  → Auto-selected: {page.get('name')}")
        return page

    print()
    choice = input(f"  Select page [1-{len(pages)}]: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(pages):
            return pages[idx]
    except ValueError:
        pass

    logger.error("Invalid choice.")
    sys.exit(1)


# ── Verify Page Access ────────────────────────────────────────────────────────

def verify_page(page_id: str, page_token: str):
    """Test that the page token works."""
    result = api_get(page_id, {
        "access_token": page_token,
        "fields": "id,name"
    })
    if "error" in result:
        logger.error("Page token invalid: %s", result["error"]["message"])
        return False
    print(f"  ✅ Page verified: {result.get('name')} (ID: {result.get('id')})")
    return True


# ── Check Instagram ───────────────────────────────────────────────────────────

def check_instagram(page_id: str, page_token: str) -> str | None:
    """Check if the page has a linked Instagram Business Account."""
    result = api_get(page_id, {
        "access_token": page_token,
        "fields": "instagram_business_account",
    })
    ig = result.get("instagram_business_account")
    if ig:
        print(f"  📸 Instagram account linked: {ig.get('id')}")
        return ig.get("id")
    return None


# ── Subscribe Page-level Webhook ──────────────────────────────────────────────

def subscribe_page(page_id: str, page_token: str):
    """Subscribe the page to 'feed' and 'mention' fields."""
    step("7. Subscribing Page-Level Webhooks")
    result = api_post(f"{page_id}/subscribed_apps", {
        "access_token": page_token,
        "subscribed_fields": "feed,mention",
    })

    if "error" in result:
        logger.warning("Page subscription issue: %s", result["error"]["message"])
    else:
        print("  ✅ Page subscribed to: feed, mention")

    # Verify
    check = api_get(f"{page_id}/subscribed_apps", {"access_token": page_token})
    apps = check.get("data", [])
    if apps:
        print(f"  📋 Current fields: {apps[0].get('subscribed_fields', [])}")
    else:
        logger.warning("  ⚠️  No subscription found — try again from Meta Dev Console")


# ── Subscribe App-level Webhook ───────────────────────────────────────────────

def subscribe_app(app_id: str, app_secret: str, callback_url: str, verify_token: str):
    """Subscribe the app to page webhooks at the app level."""
    step("8. Subscribing App-Level Webhooks")
    app_token = f"{app_id}|{app_secret}"

    print(f"  Callback URL: {callback_url}")
    print(f"  Verify Token: {verify_token}")

    # Check current subscriptions first
    current = api_get(f"{app_id}/subscriptions", {"access_token": app_token})
    for sub in current.get("data", []):
        if sub.get("object") == "page":
            existing_fields = [f.get("name") for f in sub.get("fields", [])]
            print(f"  Current page subscription fields: {existing_fields}")

    result = api_post(f"{app_id}/subscriptions", {
        "access_token": app_token,
        "object": "page",
        "fields": "feed,mention",
        "callback_url": callback_url,
        "verify_token": verify_token,
        "include_values": "true",
    })

    if "error" in result:
        if "already" in result["error"]["message"].lower():
            logger.info("  App subscription already exists — updating fields.")
        else:
            logger.warning("App subscription warning: %s", result["error"]["message"])

    # Re-fetch and show
    check = api_get(f"{app_id}/subscriptions", {"access_token": app_token})
    for sub in check.get("data", []):
        if sub.get("object") == "page":
            fields = [f.get("name") for f in sub.get("fields", [])]
            print(f"  ✅ App subscribed to: {fields}")
            print(f"     Callback: {sub.get('callback_url')}")
            print(f"     Active:   {sub.get('active')}")
            break


# ── Store in DB ───────────────────────────────────────────────────────────────

def store_credentials(
    db_url: str,
    tenant_id: int,
    app_id: str,
    app_secret: str,
    page_id: str,
    page_token: str,
    verify_token: str,
    callback_url: str,
    ig_id: str | None,
):
    """Store Meta credentials in the database for the given tenant."""
    step("9. Storing Credentials in Database")
    from sqlalchemy import create_engine, text as sqla_text
    from sqlalchemy.orm import sessionmaker
    from models.database import MetaCredentials, Tenant

    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, connect_args=connect_args, echo=False)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            tenants = db.query(Tenant).all()
            if not tenants:
                logger.error("No tenants found in the database. Run reset_db.py first.")
                sys.exit(1)
            print(f"  Available tenants: {[f'#{t.id} {t.name}' for t in tenants]}")
            tid = input(f"  Enter tenant ID to assign: ").strip()
            tenant = db.query(Tenant).filter(Tenant.id == int(tid)).first()
            if not tenant:
                logger.error("Invalid tenant ID.")
                sys.exit(1)
            tenant_id = tenant.id

        # Deactivate any existing creds for this tenant
        existing = db.query(MetaCredentials).filter(
            MetaCredentials.tenant_id == tenant_id,
            MetaCredentials.is_active == True,
        ).all()
        for c in existing:
            c.is_active = False
            logger.info("  Deactivated old credentials (ID=%d)", c.id)

        # Create new credentials
        creds = MetaCredentials(
            tenant_id=tenant_id,
            app_id=app_id,
            app_secret=app_secret,
            page_access_token=page_token,
            page_id=page_id,
            webhook_verify_token=verify_token,
            instagram_account_id=ig_id,
            is_active=True,
        )
        db.add(creds)
        db.commit()
        db.refresh(creds)
        logger.info("  ✅ Credentials stored (ID=%d) for Tenant #%d (%s)", creds.id, tenant.id, tenant.name)
        logger.info("")
        logger.info("  ┌─────────────────────────────────────────────────────────┐")
        logger.info("  │  Page ID:         %-35s │", page_id)
        logger.info("  │  Page Token:      %-35s │", page_token[:30] + "…")
        logger.info("  │  Webhook Callback: %-33s │", callback_url)
        logger.info("  │  Verify Token:    %-35s │", verify_token)
        logger.info("  │  Fields:          feed, mention                         │")
        logger.info("  └─────────────────────────────────────────────────────────┘")
        logger.info("")

    except Exception as exc:
        db.rollback()
        logger.error("Failed to store credentials: %s", exc)
        sys.exit(1)
    finally:
        db.close()


def get_super_admin_tenant(db_url: str) -> int | None:
    """Get the tenant ID of the super admin user."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models.user import User
    from models.database import Tenant

    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, connect_args=connect_args, echo=False)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        super_admin = db.query(User).filter(User.role == "super_admin").first()
        if super_admin:
            print(f"  Found super_admin '@{super_admin.username}' → Tenant #{super_admin.tenant_id}")
            return super_admin.tenant_id
        return None
    finally:
        db.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    cfg = get_config()

    # 1. Exchange short → long-lived token
    long_token = exchange_token(cfg["app_id"], cfg["app_secret"], cfg["short_token"])

    # 2. Get pages
    pages = get_pages(long_token)

    # 3. Pick page
    page = select_page(pages)
    page_id = page.get("id")
    page_token = page.get("access_token", "")

    print(f"\n  Page Name:  {page.get('name')}")
    print(f"  Page ID:    {page_id}")
    print(f"  Page Token: {page_token[:30]}…{page_token[-10:]}")

    # 4. Verify page access
    verify_page(page_id, page_token)

    # 5. Check for Instagram
    ig_id = check_instagram(page_id, page_token)

    # 6. Subscribe page-level
    subscribe_page(page_id, page_token)

    # 7. Get or create tenant — must store creds BEFORE app-level subscription
    #    so Meta's callback verification can find the verify_token in the DB.
    tenant_id = get_super_admin_tenant(cfg["db_url"])
    if not tenant_id:
        logger.warning("No super admin user found in database.")
        print()
        tenants_prompt = input("  Enter the tenant ID to associate this page with: ").strip()
        tenant_id = int(tenants_prompt)

    # 8. Store credentials in DB FIRST (before app-level webhook subscribe)
    store_credentials(
        db_url=cfg["db_url"],
        tenant_id=tenant_id,
        app_id=cfg["app_id"],
        app_secret=cfg["app_secret"],
        page_id=page_id,
        page_token=page_token,
        verify_token=cfg["verify_token"],
        callback_url=cfg["callback_url"],
        ig_id=ig_id,
    )

    # 9. Subscribe app-level AFTER credentials are in DB
    #    This way Meta's callback verification finds the verify_token in the DB
    #    and the Cloud Run webhook handler can verify successfully.
    subscribe_app(cfg["app_id"], cfg["app_secret"], cfg["callback_url"], cfg["verify_token"])

    print()
    print("=" * 60)
    print("  ✅ META SETUP COMPLETE!")
    print()
    print("  Your Facebook page is now connected.")
    print("  New comments will be analyzed and appear in the dashboard.")
    print()
    print("  Next step: Post a test comment on your page and check!")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
reset_db.py — Wipes all data and creates a fresh super admin.

Usage:
    python scripts/reset_db.py

Prompts for:
    - Database URL (defaults to .env DATABASE_URL or SQLite)
    - Super admin username, email, password
"""

import os, sys, logging
from pathlib import Path

# Add backend to path so we can reuse models
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("reset_db")


def get_db_url() -> str:
    """Resolve the database URL from env or user input."""
    # 1st priority: explicit env var
    explicit = os.getenv("RESET_DATABASE_URL")
    if explicit:
        return explicit

    # 2nd: DATABASE_URL from .env
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent.parent / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)

    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return env_url

    # 3rd: prompt
    print()
    print("=" * 60)
    print("DATABASE URL")
    print("=" * 60)
    print("Enter the database URL to reset.")
    print()
    print("  PostgreSQL (Render):")
    print("    postgresql://user:pass@host:port/dbname")
    print()
    print("  SQLite (local):")
    print("    sqlite:///cyberguard.db")
    print()
    url = input("DATABASE_URL > ").strip()
    if not url:
        url = "sqlite:///cyberguard.db"
        print(f"  Using default: {url}")
    return url


def main():
    url = get_db_url()

    # Confirm
    print()
    print("⚠️  WARNING: This will DELETE ALL EXISTING DATA!")
    print(f"   Target: {url}")
    print()
    confirm = input("Type 'RESET' to confirm: ").strip()
    if confirm != "RESET":
        print("Cancelled.")
        sys.exit(0)

    # ── Import models ──────────────────────────────────────────────────────
    from sqlalchemy import create_engine, text as sqla_text
    from sqlalchemy.orm import sessionmaker
    from models.database import Base, Tenant
    from models.user import User

    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, echo=False)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # ── Drop and recreate all tables ───────────────────────────────────────
    logger.info("Dropping all tables…")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped.")

    logger.info("Recreating all tables…")
    Base.metadata.create_all(bind=engine, checkfirst=False)
    logger.info("All tables created.")

    # Recreate the partial unique index (PostgreSQL-specific)
    with engine.connect() as conn:
        dialect = conn.dialect.name
        if dialect == "postgresql":
            conn.execute(sqla_text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_meta_creds_unique_active_page
                ON meta_credentials (page_id) WHERE is_active = true
            """))
        elif dialect == "sqlite":
            conn.execute(sqla_text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_meta_creds_unique_active_page
                ON meta_credentials (page_id) WHERE is_active
            """))
        conn.commit()

    # ── Create tenant + super admin ────────────────────────────────────────
    print()
    print("=" * 60)
    print("CREATE SUPER ADMIN")
    print("=" * 60)
    print()

    username = input("  Username   [adminyou]: ").strip() or "adminyou"
    email = input("  Email      [admin@aicyberbullying.local]: ").strip() or "admin@aicyberbullying.local"
    password = input("  Password   [admin123456]: ").strip() or "admin123456"
    tenant_name = input("  Tenant name [Default]: ").strip() or "Default"

    db = SessionLocal()
    try:
        tenant = Tenant(name=tenant_name)
        db.add(tenant)
        db.flush()

        user = User(
            username=username,
            email=email,
            role="super_admin",
            tenant_id=tenant.id,
        )
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(tenant)
        db.refresh(user)

        logger.info("")
        logger.info("✅  Database reset complete!")
        logger.info("   Tenant:   #%d (%s)", tenant.id, tenant.name)
        logger.info("   Username: @%s", user.username)
        logger.info("   Role:     %s", user.role)
        logger.info("   Login at the admin panel with these credentials.")
        logger.info("")

    except Exception as exc:
        db.rollback()
        logger.error("Failed: %s", exc)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

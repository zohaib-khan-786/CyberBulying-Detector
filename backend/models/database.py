"""
database.py — SQLAlchemy models + session factory.

Uses SQLite by default (zero config, no server needed).
Set DATABASE_URL in .env to swap in MySQL or PostgreSQL:
  mysql+mysqlconnector://user:pass@host/cyberguard
  postgresql://user:pass@host/cyberguard
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List
from pathlib import Path

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer,
    String, Text, create_engine, event, pool,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ── Engine ─────────────────────────────────────────────────────────────────────

_DEFAULT_DB = "sqlite:///" + str(Path(__file__).parent.parent / "cyberguard.db")
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
_pool_kwargs = (
    {"poolclass": pool.NullPool}
    if DATABASE_URL.startswith("sqlite")
    else {"pool_size": 10, "max_overflow": 20, "pool_recycle": 1800, "pool_pre_ping": True}
)
engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False, **_pool_kwargs)

# Enable WAL mode for SQLite so reads don't block writes
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_wal(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ── Base ───────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Models ─────────────────────────────────────────────────────────────────────

class Flag(Base):
    """Every piece of text analysed and found harmful."""
    __tablename__ = "flags"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    text          = Column(Text,    nullable=False)
    label         = Column(String(32),  nullable=False)
    label_id      = Column(Integer,     nullable=False)
    confidence    = Column(Float,       nullable=False)
    severity      = Column(String(16),  nullable=False)
    color         = Column(String(10),  nullable=False)
    is_harmful    = Column(Boolean,     default=True)
    source        = Column(String(32),  default="manual")   # manual | facebook | instagram
    author        = Column(String(128), default="anonymous")
    author_id     = Column(String(128), nullable=True)   # Facebook/Instagram user ID for blocking
    platform      = Column(String(32),  nullable=True)
    comment_id    = Column(String(128), nullable=True)
    trigger_words = Column(Text,        nullable=True)       # JSON list of trigger words
    auto_flagged  = Column(Boolean,     default=False)
    created_at    = Column(DateTime,    default=lambda: datetime.now(timezone.utc))

    # Moderation state
    mod_status    = Column(String(16),  default="pending")   # pending | reviewed | actioned | dismissed
    mod_action    = Column(String(16),  nullable=True)        # delete | warn | block | None
    mod_note      = Column(Text,        nullable=True)
    moderated_at  = Column(DateTime,    nullable=True)
    moderated_by  = Column(String(64),  nullable=True)        # admin username (future JWT)

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "text":         self.text,
            "label":        self.label,
            "label_id":     self.label_id,
            "confidence":   self.confidence,
            "severity":     self.severity,
            "color":        self.color,
            "is_harmful":   self.is_harmful,
            "trigger_words": json.loads(self.trigger_words) if self.trigger_words else [],
            "source":       self.source,
            "author":       self.author,
            "author_id":    self.author_id,
            "platform":     self.platform,
            "comment_id":   self.comment_id,
            "auto_flagged": self.auto_flagged,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "timestamp":    int(self.created_at.timestamp()) if self.created_at else None,
            "mod_status":   self.mod_status,
            "mod_action":   self.mod_action,
            "mod_note":     self.mod_note,
        }


class ModeratedUser(Base):
    """Tracks users who have received a moderation action."""
    __tablename__ = "moderated_users"

    id          = Column(Integer,    primary_key=True, autoincrement=True)
    username    = Column(String(128), nullable=False, index=True)
    platform    = Column(String(32),  nullable=False)
    action      = Column(String(16),  nullable=False)   # warn | block
    reason      = Column(Text,        nullable=True)
    flag_id     = Column(Integer,     nullable=True)    # FK to flags.id (soft ref)
    created_at  = Column(DateTime,    default=lambda: datetime.now(timezone.utc))
    expires_at  = Column(DateTime,    nullable=True)    # None = permanent
    is_active   = Column(Boolean,     default=True)
    actioned_by = Column(String(64),  nullable=True)

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "username":   self.username,
            "platform":   self.platform,
            "action":     self.action,
            "reason":     self.reason,
            "flag_id":    self.flag_id,
            "is_active":  self.is_active,
            "created_at": int(self.created_at.timestamp()) if self.created_at else None,
            "expires_at": int(self.expires_at.timestamp()) if self.expires_at else None,
            "actioned_by": self.actioned_by,
        }


class TimeSeriesPoint(Base):
    """Hourly aggregated flag counts — powers the dashboard timeline chart."""
    __tablename__ = "timeseries"

    id        = Column(Integer,  primary_key=True, autoincrement=True)
    hour      = Column(DateTime, nullable=False, index=True)   # truncated to hour
    label     = Column(String(32), nullable=False)
    count     = Column(Integer,  default=0)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_db() -> Session:
    """Yield a DB session; caller must close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

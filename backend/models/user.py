"""
User model — SQLAlchemy ORM for multi-user authentication.

Fields:
  id, username, email, password_hash, role, is_active, created_at
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import bcrypt
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from models.database import Base


class User(Base):
    """Application user with bcrypt password hashing."""

    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(64),  nullable=False, unique=True, index=True)
    email         = Column(String(256), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)
    role          = Column(String(16),  nullable=False, default="user")  # admin | user
    is_active     = Column(Boolean,     default=True)
    created_at    = Column(DateTime,    default=lambda: datetime.now(timezone.utc))

    # ── Password helpers ──────────────────────────────────────────────────────

    def set_password(self, raw_password: str) -> None:
        """Hash and store the password."""
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        """Verify a password against the stored hash."""
        return bcrypt.checkpw(
            raw_password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "username":   self.username,
            "email":      self.email,
            "role":       self.role,
            "is_active":  self.is_active,
            "created_at": int(self.created_at.timestamp()) if self.created_at else None,
        }

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def validate_username(username: str) -> str | None:
        """Return error message or None if valid."""
        if not username or len(username) < 3:
            return "Username must be at least 3 characters."
        if len(username) > 64:
            return "Username must be 64 characters or fewer."
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            return "Username may only contain letters, digits, and underscores."
        return None

    @staticmethod
    def validate_email(email: str) -> str | None:
        if not email or "@" not in email:
            return "A valid email address is required."
        if len(email) > 256:
            return "Email must be 256 characters or fewer."
        return None

    @staticmethod
    def validate_password(password: str) -> str | None:
        if not password or len(password) < 8:
            return "Password must be at least 8 characters."
        if len(password) > 128:
            return "Password must be 128 characters or fewer."
        return None

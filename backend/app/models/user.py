"""
app/models/user.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    In a SaaS platform, everything orbits the User. We need a persistent
    store for user preferences, Gmail connection state, and unique identifiers
    provided by external auth providers (like Clerk).

WHAT IT DOES
    Defines the `User` model which:
    - Stores the `clerk_id` to link with the external auth provider.
    - Tracks Gmail connection status and sync preferences.
    - Stores onboarding progress (so users return to where they left off).
    - Acts as the parent for all tasks, approvals, and logs (multi-tenancy).

HOW IT CONNECTS
    - Task model      → many-to-one (one user has many tasks)
    - Approval model  → many-to-one (one user has many approvals)
    - Gmail endpoints → checks user connection status here
"""

import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING, List
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.approval import Approval
    from app.models.gmail import OAuthToken


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # ── Gmail Connection ──────────────────────────────────────────────────────
    is_gmail_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    gmail_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gmail_access_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gmail_refresh_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gmail_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # ── Product State ────────────────────────────────────────────────────────
    has_completed_onboarding: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[str] = mapped_column(String(50), default="welcome")
    
    # Preferences
    preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=dict)

    # ── Relationships ─────────────────────────────────────────────────────────
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="user", cascade="all, delete-orphan")
    oauth_tokens: Mapped[List["OAuthToken"]] = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

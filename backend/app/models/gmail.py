"""
app/models/gmail.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    To store the state of our Gmail integration. We need to remember which
    emails we've processed, store OAuth tokens to access the Gmail API, and
    track the ingestion logs.

WHAT IT DOES
    Defines SQLAlchemy models:
    - OAuthToken: Stores access and refresh tokens for Google API access.
    - EmailMessage: Stores metadata and parsed content of ingested emails.
    - EmailThread: Groups emails together logically.
    - IngestionLog: Records the polling history and any errors during ingestion.

HOW IT CONNECTS
    The ingestion pipeline reads from the Gmail API, saves `EmailMessage` records,
    and then queues `Task` records.
"""

import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin

class OAuthToken(Base, TimestampMixin):
    """Stores Google OAuth2 tokens securely for each user."""
    __tablename__ = "oauth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="google", index=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    scopes: Mapped[str] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=True)

    user = relationship("User", back_populates="oauth_tokens")

    __table_args__ = (
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )


class EmailThread(Base, TimestampMixin):
    """Groups emails into threads (conversations)."""
    __tablename__ = "email_threads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    gmail_thread_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    messages: Mapped[list["EmailMessage"]] = relationship(
        "EmailMessage", back_populates="thread", cascade="all, delete-orphan"
    )


class EmailMessage(Base, TimestampMixin):
    """Represents a single parsed email ingested from Gmail."""
    __tablename__ = "email_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    thread_id: Mapped[Uuid | None] = mapped_column(Uuid, ForeignKey("email_threads.id"), nullable=True)
    
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_plain: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    
    # Track the processing lifecycle of this email
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED", index=True)
    
    # Link to the Task generated for this email
    task_id: Mapped[Uuid | None] = mapped_column(Uuid, ForeignKey("tasks.id"), nullable=True)

    thread: Mapped["EmailThread"] = relationship("EmailThread", back_populates="messages")


class IngestionLog(Base, TimestampMixin):
    """Audit log specifically for the email polling process."""
    __tablename__ = "ingestion_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "SUCCESS", "FAILED"
    emails_fetched: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

"""Initial migration: create tasks, agents, and logs tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-05-08

This migration creates the three core tables for the Agentic Task Router.
It is intentionally written explicitly (not auto-generated) so you can
understand exactly what Alembic produces — and so it serves as a reference.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ─────────────────────────────────────────────────────────────────────────────
revision: str = "001_initial"
down_revision: Union[str, None] = None   # This is the first migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ─────────────────────────────────────────────────────────────────────────────


def upgrade() -> None:
    """Apply the migration — create all tables and indexes."""

    # ── ENUM TYPES ─────────────────────────────────────────────────────────────
    # We remove explicit enum creation and let sa.Enum create it if necessary
    # PostgreSQL uses native ENUM types for efficiency and constraint enforcement

    # ── AGENTS TABLE ───────────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "type",
            sa.Enum("llm", "tool", "human", "router", name="agent_type_enum"),
            nullable=False,
        ),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_concurrent_tasks", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agents_name", "agents", ["name"])
    op.create_index("ix_agents_is_active", "agents", ["is_active"])
    op.create_index("ix_agents_created_at", "agents", ["created_at"])

    # ── TASKS TABLE ────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "in_progress", "completed", "failed", "cancelled", name="task_status_enum"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "assigned_agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_is_deleted", "tasks", ["is_deleted"])
    op.create_index("ix_tasks_assigned_agent_id", "tasks", ["assigned_agent_id"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])
    op.create_index("ix_tasks_status_created_at", "tasks", ["status", "created_at"])
    op.create_index("ix_tasks_agent_status", "tasks", ["assigned_agent_id", "status"])

    # ── LOGS TABLE ─────────────────────────────────────────────────────────────
    op.create_table(
        "logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("debug", "info", "warning", "error", "critical", name="log_level_enum"),
            nullable=False,
            server_default="info",
        ),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_logs_task_id", "logs", ["task_id"])
    op.create_index("ix_logs_level", "logs", ["level"])
    op.create_index("ix_logs_timestamp", "logs", ["timestamp"])


def downgrade() -> None:
    """Roll back the migration — drop all tables and types in reverse order."""

    # Drop in reverse dependency order
    op.drop_table("logs")
    op.drop_table("tasks")
    op.drop_table("agents")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS log_level_enum")
    op.execute("DROP TYPE IF EXISTS task_status_enum")
    op.execute("DROP TYPE IF EXISTS agent_type_enum")

"""Add HITL approvals table and AWAITING_APPROVAL task status

Revision ID: 006
Revises: 005
Create Date: 2026-05-09 03:00:00.000000

WHY THIS MIGRATION EXISTS
    Implements the Human-in-the-Loop database layer:

    1. `approvals` table: The central HITL store. Each row represents one
       workflow pause checkpoint with full serialized graph state, the AI
       draft under review, and the human's eventual decision.

    2. `approval_status_enum`: Postgres native enum for the decision lifecycle
       (PENDING_APPROVAL, APPROVED, EDITED, REJECTED, EXPIRED).

    3. Extends `task_status_enum` with `awaiting_approval` so tasks can
       visibly reflect their paused state in the UI.

    4. Indexes on (status, created_at) and (task_id, status) for fast
       queue queries and task-level approval lookups.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Extend task_status_enum with awaiting_approval ────────────────────
    # PostgreSQL requires ALTER TYPE to add new enum values.
    # We use BEFORE to place it logically in the lifecycle order.
    op.execute("ALTER TYPE task_status_enum ADD VALUE IF NOT EXISTS 'awaiting_approval' BEFORE 'completed'")

    # ── 2. Create approval_status_enum ───────────────────────────────────────
    approval_status_enum = postgresql.ENUM(
        "pending_approval",
        "approved",
        "edited",
        "rejected",
        "expired",
        name="approval_status_enum",
        create_type=True,
    )
    approval_status_enum.create(op.get_bind(), checkfirst=True)

    # ── 3. Create the approvals table ────────────────────────────────────────
    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "task_id",
            sa.Uuid(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # AI content under review
        sa.Column("ai_generated_draft", sa.Text(), nullable=True),
        sa.Column("original_input", sa.Text(), nullable=True),
        sa.Column("workflow_context", postgresql.JSONB(), nullable=True),
        sa.Column("graph_checkpoint_state", postgresql.JSONB(), nullable=True),
        sa.Column("checkpoint_node", sa.String(255), nullable=True),
        # Decision
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending_approval", "approved", "edited", "rejected", "expired",
                name="approval_status_enum",
                create_type=False,  # Already created above
            ),
            nullable=False,
            server_default="pending_approval",
        ),
        sa.Column("human_edited_content", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        # Reviewer identity (RBAC-ready)
        sa.Column("reviewer_id", sa.String(255), nullable=True),
        sa.Column("reviewer_name", sa.String(255), nullable=True),
        # Timing audit trail
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resume_task_id", sa.String(255), nullable=True),
        # Standard timestamps (from TimestampMixin)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # ── 4. Indexes ────────────────────────────────────────────────────────────
    op.create_index("ix_approvals_task_id", "approvals", ["task_id"])
    op.create_index("ix_approvals_status", "approvals", ["status"])
    op.create_index(
        "ix_approvals_status_created_at",
        "approvals",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_approvals_task_status",
        "approvals",
        ["task_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_approvals_task_status", table_name="approvals")
    op.drop_index("ix_approvals_status_created_at", table_name="approvals")
    op.drop_index("ix_approvals_status", table_name="approvals")
    op.drop_index("ix_approvals_task_id", table_name="approvals")
    op.drop_table("approvals")
    op.execute("DROP TYPE IF EXISTS approval_status_enum")

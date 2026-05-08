"""Add users table and link to tasks and approvals (multi-tenancy)

Revision ID: 007
Revises: 006
Create Date: 2026-05-09 05:00:00.000000

WHY THIS MIGRATION EXISTS
    Transforms the platform from a single-tenant admin dashboard into a 
    multi-tenant SaaS product. Every task and approval must now belong to a 
    specific user.

WHAT IT DOES
    1. Creates the `users` table to store Clerk IDs and Gmail tokens.
    2. Adds `user_id` column to `tasks`.
    3. Adds `user_id` column to `approvals`.
    4. Creates foreign key constraints and indexes for high-performance 
       user-scoped querying.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create Users Table ────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("clerk_id", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_gmail_connected", sa.Boolean(), server_default="false"),
        sa.Column("gmail_email", sa.String(255), nullable=True),
        sa.Column("gmail_access_token", sa.String(255), nullable=True),
        sa.Column("gmail_refresh_token", sa.String(255), nullable=True),
        sa.Column("gmail_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("has_completed_onboarding", sa.Boolean(), server_default="false"),
        sa.Column("onboarding_step", sa.String(50), server_default="welcome"),
        sa.Column("preferences", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_clerk_id", "users", ["clerk_id"], unique=True)

    # ── 2. Add user_id to Tasks ──────────────────────────────────────────────
    op.add_column("tasks", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_user_id", "tasks", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])

    # ── 3. Add user_id to Approvals ──────────────────────────────────────────
    op.add_column("approvals", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_approvals_user_id", "approvals", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_approvals_user_id", "approvals", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_approvals_user_id", table_name="approvals")
    op.drop_constraint("fk_approvals_user_id", "approvals", type_="foreignkey")
    op.drop_column("approvals", "user_id")

    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_constraint("fk_tasks_user_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "user_id")

    op.drop_index("ix_users_clerk_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

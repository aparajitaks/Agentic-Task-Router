"""Add missing task statuses

Revision ID: 20260510_0146
Revises: ebd0094234a4
Create Date: 2026-05-10 01:46:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260510_0146'
down_revision: Union[str, None] = 'ebd0094234a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing task status enum values one by one
    # We use 'IF NOT EXISTS' to be idempotent just in case
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE task_status_enum ADD VALUE IF NOT EXISTS 'queued'")
        op.execute("ALTER TYPE task_status_enum ADD VALUE IF NOT EXISTS 'processing'")
        op.execute("ALTER TYPE task_status_enum ADD VALUE IF NOT EXISTS 'retrying'")


def downgrade() -> None:
    # Postgres does not support DROP VALUE from enum natively.
    # To properly downgrade, we would have to recreate the enum type.
    # For this project, we can leave them in the DB.
    pass

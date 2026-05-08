"""Add async celery tracking fields

Revision ID: 003
Revises: 002
Create Date: 2026-05-08 17:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new celery execution columns to tasks table
    op.add_column('tasks', sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('tasks', sa.Column('execution_started_at', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('execution_completed_at', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('worker_id', sa.String(length=255), nullable=True))
    op.add_column('tasks', sa.Column('failure_reason', sa.Text(), nullable=True))

def downgrade() -> None:
    # Remove the columns
    op.drop_column('tasks', 'failure_reason')
    op.drop_column('tasks', 'worker_id')
    op.drop_column('tasks', 'execution_completed_at')
    op.drop_column('tasks', 'execution_started_at')
    op.drop_column('tasks', 'retry_count')

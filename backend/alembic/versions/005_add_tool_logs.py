"""Add tool execution logs

Revision ID: 005
Revises: 004
Create Date: 2026-05-08 19:42:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('tool_execution_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('arguments', sa.JSON(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('is_success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_execution_logs_task_id'), 'tool_execution_logs', ['task_id'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_tool_name'), 'tool_execution_logs', ['tool_name'], unique=False)

def downgrade() -> None:
    op.drop_table('tool_execution_logs')

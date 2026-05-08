"""Add workflow state columns to Task

Revision ID: 002
Revises: 001
Create Date: 2026-05-08 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add input_text, output_text, route_taken to tasks table
    op.add_column('tasks', sa.Column('input_text', sa.Text(), nullable=True))
    op.add_column('tasks', sa.Column('output_text', sa.Text(), nullable=True))
    op.add_column('tasks', sa.Column('route_taken', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('tasks', 'route_taken')
    op.drop_column('tasks', 'output_text')
    op.drop_column('tasks', 'input_text')

"""Add gmail integration tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-08 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. oauth_tokens
    op.create_table('oauth_tokens',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_tokens_provider'), 'oauth_tokens', ['provider'], unique=True)
    op.create_index(op.f('ix_oauth_tokens_created_at'), 'oauth_tokens', ['created_at'], unique=False)

    # 2. email_threads
    op.create_table('email_threads',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('gmail_thread_id', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_threads_gmail_thread_id'), 'email_threads', ['gmail_thread_id'], unique=True)
    op.create_index(op.f('ix_email_threads_created_at'), 'email_threads', ['created_at'], unique=False)

    # 3. email_messages
    op.create_table('email_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('gmail_message_id', sa.String(length=255), nullable=False),
        sa.Column('thread_id', sa.Uuid(), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('body_plain', sa.Text(), nullable=True),
        sa.Column('has_attachments', sa.Boolean(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['thread_id'], ['email_threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_messages_gmail_message_id'), 'email_messages', ['gmail_message_id'], unique=True)
    op.create_index(op.f('ix_email_messages_status'), 'email_messages', ['status'], unique=False)
    op.create_index(op.f('ix_email_messages_created_at'), 'email_messages', ['created_at'], unique=False)

    # 4. ingestion_logs
    op.create_table('ingestion_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('emails_fetched', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingestion_logs_created_at'), 'ingestion_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('ingestion_logs')
    op.drop_table('email_messages')
    op.drop_table('email_threads')
    op.drop_table('oauth_tokens')

"""Add email thread support

Revision ID: add_email_thread_support
Revises: b47ce93dbad9
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_email_thread_support'
down_revision = 'b47ce93dbad9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add thread_id column to email_messages table
    op.add_column('email_messages', sa.Column('thread_id', sa.String(length=255), nullable=True))
    
    # Add index on thread_id for efficient thread-based queries
    op.create_index('ix_email_messages_thread_id', 'email_messages', ['thread_id'])
    
    # Add thread_message_count to track number of messages in thread
    op.add_column('email_messages', sa.Column('thread_message_count', sa.Integer(), nullable=True, default=1))
    
    # Add is_thread_root to identify the first message in a thread
    op.add_column('email_messages', sa.Column('is_thread_root', sa.Boolean(), nullable=True, default=True))


def downgrade() -> None:
    # Remove the added columns and index
    op.drop_index('ix_email_messages_thread_id', table_name='email_messages')
    op.drop_column('email_messages', 'thread_id')
    op.drop_column('email_messages', 'thread_message_count')
    op.drop_column('email_messages', 'is_thread_root')

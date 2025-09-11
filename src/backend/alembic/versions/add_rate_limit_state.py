"""Add rate_limit_state table for persistent limiter

Revision ID: add_rate_limit_state
Revises: add_backlink_indexes
Create Date: 2025-09-11
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_rate_limit_state'
down_revision = 'add_backlink_indexes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'rate_limit_state',
        sa.Column('name', sa.String(length=50), primary_key=True),
        sa.Column('tokens', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('rate_per_minute', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade() -> None:
    op.drop_table('rate_limit_state')
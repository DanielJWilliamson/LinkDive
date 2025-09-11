"""Add performance indexes for backlink results

Revision ID: add_backlink_indexes
Revises: f3c2b1c4a210
Create Date: 2025-09-11
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_backlink_indexes'
down_revision = 'f3c2b1c4a210'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index('ix_backlink_campaign_status', 'backlink_results', ['campaign_id', 'coverage_status'])
    op.create_index('ix_backlink_campaign_destination', 'backlink_results', ['campaign_id', 'link_destination'])

def downgrade() -> None:
    op.drop_index('ix_backlink_campaign_status', table_name='backlink_results')
    op.drop_index('ix_backlink_campaign_destination', table_name='backlink_results')
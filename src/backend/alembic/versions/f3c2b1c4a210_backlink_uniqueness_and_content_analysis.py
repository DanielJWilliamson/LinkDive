"""Add backlink uniqueness, link_destination, content analysis tables

Revision ID: f3c2b1c4a210
Revises: 87a1b9bfe049
Create Date: 2025-09-10 10:05:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f3c2b1c4a210'
down_revision: Union[str, Sequence[str], None] = '87a1b9bfe049'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new column link_destination & unique constraint to backlink_results
    with op.batch_alter_table('backlink_results') as batch_op:
        batch_op.add_column(sa.Column('link_destination', sa.String(length=30), nullable=True))
    op.create_unique_constraint('uq_backlink_unique', 'backlink_results', ['campaign_id', 'url', 'source_api'])
    # Add last_backlink_fetch_at to campaigns if not present
    with op.batch_alter_table('campaigns') as batch_op:
        batch_op.add_column(sa.Column('last_backlink_fetch_at', sa.DateTime(timezone=True), nullable=True))

    # Content analysis table
    op.create_table(
        'content_analysis',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('backlink_result_id', sa.Integer(), sa.ForeignKey('backlink_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('keyword_hits', sa.JSON(), nullable=True),
        sa.Column('score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('hash', sa.String(length=64), nullable=True, index=True),
        sa.Column('raw_excerpt', sa.Text(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
    )


def downgrade() -> None:
    op.drop_table('content_analysis')
    op.drop_constraint('uq_backlink_unique', 'backlink_results', type_='unique')
    with op.batch_alter_table('backlink_results') as batch_op:
        batch_op.drop_column('link_destination')
    with op.batch_alter_table('campaigns') as batch_op:
        batch_op.drop_column('last_backlink_fetch_at')

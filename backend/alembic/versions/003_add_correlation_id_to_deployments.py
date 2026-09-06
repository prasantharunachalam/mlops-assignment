"""Add correlation_id to deployments

Revision ID: 003
Revises: 002
Create Date: 2026-09-06 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add correlation_id column to track requests through async processing
    op.add_column('deployments', sa.Column('correlation_id', sa.String(), nullable=True))
    op.create_index('ix_deployments_correlation_id', 'deployments', ['correlation_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_deployments_correlation_id', table_name='deployments')
    op.drop_column('deployments', 'correlation_id')

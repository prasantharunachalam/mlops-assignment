"""Add composite index for rollback queries

Revision ID: 002
Revises: 001
Create Date: 2026-09-06 14:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add composite index to optimize rollback queries
    # This index supports the query in deployment_repository.py:85-90
    # which filters by (model_version_id, environment, status, completed_at)
    op.create_index(
        'ix_deployments_rollback_lookup',
        'deployments',
        ['model_version_id', 'environment', 'status', 'completed_at'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_deployments_rollback_lookup', table_name='deployments')

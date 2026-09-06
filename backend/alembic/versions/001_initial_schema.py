"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create models table
    op.create_table(
        'models',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create model_versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('version_number', sa.String(), nullable=False),
        sa.Column('framework', sa.String(), nullable=False),
        sa.Column('algorithm', sa.String(), nullable=True),
        sa.Column('artifact_uri', sa.String(), nullable=False),
        sa.Column('training_data_ref', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('lifecycle_stage', sa.Enum('DRAFT', 'VALIDATED', 'APPROVED', 'STAGING', 'PRODUCTION', 'ARCHIVED', name='lifecyclestage'), nullable=False),
        sa.Column('row_version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_model_versions_model_id', 'model_versions', ['model_id'])
    op.create_index('ix_model_versions_lifecycle_stage', 'model_versions', ['lifecycle_stage'])

    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_version_id', sa.String(), nullable=False),
        sa.Column('environment', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('REQUESTED', 'VALIDATING', 'DEPLOYING', 'SUCCEEDED', 'FAILED', 'ROLLED_BACK', name='deploymentstatus'), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('rolled_back_from_id', sa.String(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('failure_reason', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['rolled_back_from_id'], ['deployments.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_deployments_idempotency_key')
    )
    op.create_index('ix_deployments_status_created', 'deployments', ['status', 'requested_at'])
    op.create_index('ix_deployments_environment', 'deployments', ['environment'])
    op.create_index('ix_deployments_model_version_id', 'deployments', ['model_version_id'])

    # Create metric_snapshots table
    op.create_table(
        'metric_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_version_id', sa.String(), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('throughput_rps', sa.Float(), nullable=True),
        sa.Column('error_rate', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('drift_score', sa.Float(), nullable=True),
        sa.Column('availability', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metrics_model_version_captured', 'metric_snapshots', ['model_version_id', 'captured_at'])
    op.create_index('ix_metrics_captured_at', 'metric_snapshots', ['captured_at'])


def downgrade() -> None:
    op.drop_index('ix_metrics_captured_at', table_name='metric_snapshots')
    op.drop_index('ix_metrics_model_version_captured', table_name='metric_snapshots')
    op.drop_table('metric_snapshots')

    op.drop_index('ix_deployments_model_version_id', table_name='deployments')
    op.drop_index('ix_deployments_environment', table_name='deployments')
    op.drop_index('ix_deployments_status_created', table_name='deployments')
    op.drop_table('deployments')

    op.drop_index('ix_model_versions_lifecycle_stage', table_name='model_versions')
    op.drop_index('ix_model_versions_model_id', table_name='model_versions')
    op.drop_table('model_versions')

    op.drop_table('models')

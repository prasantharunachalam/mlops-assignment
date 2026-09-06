"""
Integration tests for the complete deployment workflow.

Tests end-to-end deployment scenarios including:
- Creating deployments
- Approval gates for PRODUCTION
- STAGING-before-PRODUCTION enforcement
- Status transitions
- Environment validation
"""
import pytest
from app.models import LifecycleStage, DeploymentStatus, Deployment
from app.services import DeploymentService, RegistryService
from app.repositories import DeploymentRepository, ModelRepository
from app.schemas.deployment import DeploymentCreate


class TestDeploymentWorkflow:
    """Integration tests for deployment workflows."""

    @pytest.fixture
    def deployment_service(self, db_session):
        """Create a DeploymentService instance for testing."""
        deployment_repo = DeploymentRepository(db_session)
        model_repo = ModelRepository(db_session)
        return DeploymentService(deployment_repo, model_repo)

    @pytest.fixture
    def registry_service(self, db_session):
        """Create a RegistryService instance for testing."""
        repo = ModelRepository(db_session)
        return RegistryService(repo)

    # Basic deployment creation
    def test_deploy_approved_version_to_staging_succeeds(
        self, deployment_service, approved_version
    ):
        """Test deploying an approved version to STAGING environment."""
        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="test-staging-deploy-1"
        )

        deployment, error = deployment_service.create_deployment(deployment_data)

        assert error is None
        assert deployment is not None
        assert deployment.model_version_id == approved_version.id
        assert deployment.environment == "STAGING"
        assert deployment.status == DeploymentStatus.REQUESTED
        assert deployment.attempt_count == 1

    def test_deploy_draft_version_to_staging_succeeds(
        self, deployment_service, sample_version
    ):
        """Test deploying a draft version to STAGING (allowed for non-PRODUCTION)."""
        deployment_data = DeploymentCreate(
            model_version_id=sample_version.id,
            environment="STAGING",
            idempotency_key="test-draft-staging-1"
        )

        deployment, error = deployment_service.create_deployment(deployment_data)

        assert error is None
        assert deployment is not None
        # STAGING doesn't enforce approval gates

    def test_deploy_nonexistent_version_fails(self, deployment_service):
        """Test deploying a non-existent model version."""
        deployment_data = DeploymentCreate(
            model_version_id="nonexistent-version-id",
            environment="STAGING",
            idempotency_key="test-nonexistent-1"
        )

        deployment, error = deployment_service.create_deployment(deployment_data)

        assert deployment is None
        assert error == "Model version not found"

    # PRODUCTION approval gates
    def test_deploy_draft_to_production_fails(
        self, deployment_service, sample_version
    ):
        """Test that DRAFT versions cannot be deployed to PRODUCTION."""
        assert sample_version.lifecycle_stage == LifecycleStage.DRAFT

        deployment_data = DeploymentCreate(
            model_version_id=sample_version.id,
            environment="PRODUCTION",
            idempotency_key="test-draft-prod-1"
        )

        deployment, error = deployment_service.create_deployment(deployment_data)

        assert deployment is None
        assert error is not None
        assert "Cannot deploy DRAFT version to PRODUCTION" in error

    def test_deploy_validated_to_production_fails(
        self, deployment_service, sample_version, db_session
    ):
        """Test that VALIDATED versions cannot be deployed to PRODUCTION."""
        sample_version.lifecycle_stage = LifecycleStage.VALIDATED
        db_session.commit()
        db_session.refresh(sample_version)

        deployment_data = DeploymentCreate(
            model_version_id=sample_version.id,
            environment="PRODUCTION",
            idempotency_key="test-validated-prod-1"
        )

        deployment, error = deployment_service.create_deployment(deployment_data)

        assert deployment is None
        assert error is not None
        assert "Cannot deploy VALIDATED version to PRODUCTION" in error

    def test_deploy_approved_to_production_without_staging_fails(
        self, deployment_service, approved_version
    ):
        """Test STAGING-before-PRODUCTION enforcement."""
        assert approved_version.lifecycle_stage == LifecycleStage.APPROVED

        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="PRODUCTION",
            idempotency_key="test-prod-no-staging-1"
        )

        deployment, error = deployment_service.create_deployment(deployment_data)

        assert deployment is None
        assert error == "Version must be deployed to STAGING before PRODUCTION"

    # Complete workflow: STAGING then PRODUCTION
    def test_complete_staging_to_production_workflow(
        self, deployment_service, approved_version, db_session
    ):
        """Test complete workflow: deploy to STAGING first, then PRODUCTION."""
        # Step 1: Deploy to STAGING
        staging_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="test-workflow-staging-1"
        )
        staging_deployment, error1 = deployment_service.create_deployment(staging_data)
        assert error1 is None
        assert staging_deployment.environment == "STAGING"

        # Simulate successful STAGING deployment
        staging_deployment_obj = db_session.query(
            Deployment
        ).filter_by(id=staging_deployment.id).first()
        staging_deployment_obj.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Step 2: Deploy to PRODUCTION (should now succeed)
        prod_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="PRODUCTION",
            idempotency_key="test-workflow-prod-1"
        )
        prod_deployment, error2 = deployment_service.create_deployment(prod_data)

        assert error2 is None
        assert prod_deployment is not None
        assert prod_deployment.environment == "PRODUCTION"
        assert prod_deployment.model_version_id == approved_version.id

    def test_production_version_in_production_stage_can_deploy(
        self, deployment_service, approved_version, db_session
    ):
        """Test that versions in PRODUCTION lifecycle stage can deploy to PRODUCTION."""
        # Promote to PRODUCTION lifecycle stage
        approved_version.lifecycle_stage = LifecycleStage.PRODUCTION
        db_session.commit()

        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="PRODUCTION",
            idempotency_key="test-prod-lifecycle-1"
        )

        deployment, error = deployment_service.create_deployment(deployment_data)

        # Should succeed because PRODUCTION lifecycle stage is allowed
        assert error is None
        assert deployment is not None

    def test_staging_version_in_staging_stage_can_deploy_to_production(
        self, deployment_service, approved_version, db_session
    ):
        """Test that versions in STAGING lifecycle can deploy to PRODUCTION after STAGING deployment."""
        # First deploy to STAGING
        staging_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="test-staging-lifecycle-1"
        )
        staging_dep, _ = deployment_service.create_deployment(staging_data)

        # Mark STAGING deployment as succeeded
        staging_obj = db_session.query(
            Deployment
        ).filter_by(id=staging_dep.id).first()
        staging_obj.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Promote to STAGING lifecycle stage
        approved_version.lifecycle_stage = LifecycleStage.STAGING
        db_session.commit()

        # Deploy to PRODUCTION
        prod_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="PRODUCTION",
            idempotency_key="test-prod-from-staging-lifecycle-1"
        )
        prod_dep, error = deployment_service.create_deployment(prod_data)

        assert error is None
        assert prod_dep is not None

    # Retry functionality
    def test_retry_failed_deployment_succeeds(
        self, deployment_service, approved_version, db_session
    ):
        """Test retrying a failed deployment."""
        # Create and fail a deployment
        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="test-retry-1"
        )
        deployment, _ = deployment_service.create_deployment(deployment_data)

        # Mark as failed
        dep_obj = db_session.query(
            Deployment
        ).filter_by(id=deployment.id).first()
        dep_obj.status = DeploymentStatus.FAILED
        db_session.commit()

        # Retry the deployment
        retried, error = deployment_service.retry_deployment(deployment.id)

        assert error is None
        assert retried is not None
        assert retried.attempt_count == 2
        assert retried.status == DeploymentStatus.REQUESTED

    def test_retry_succeeded_deployment_fails(
        self, deployment_service, sample_deployment
    ):
        """Test that succeeded deployments cannot be retried."""
        assert sample_deployment.status == DeploymentStatus.SUCCEEDED

        retried, error = deployment_service.retry_deployment(sample_deployment.id)

        assert retried is None
        assert error == "Can only retry FAILED deployments"

    def test_retry_max_attempts_reached_fails(
        self, deployment_service, approved_version, db_session
    ):
        """Test that deployments cannot be retried beyond max attempts."""
        # Create a failed deployment with max attempts
        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="test-max-retry-1"
        )
        deployment, _ = deployment_service.create_deployment(deployment_data)

        # Set to failed with max attempts
        dep_obj = db_session.query(
            Deployment
        ).filter_by(id=deployment.id).first()
        dep_obj.status = DeploymentStatus.FAILED
        dep_obj.attempt_count = DeploymentService.MAX_RETRY_ATTEMPTS
        db_session.commit()

        # Try to retry
        retried, error = deployment_service.retry_deployment(deployment.id)

        assert retried is None
        assert f"Max retry attempts ({DeploymentService.MAX_RETRY_ATTEMPTS}) reached" in error

    def test_retry_nonexistent_deployment_fails(self, deployment_service):
        """Test retrying a deployment that doesn't exist."""
        retried, error = deployment_service.retry_deployment("nonexistent-id")

        assert retried is None
        assert error == "Deployment not found"

    # List and filter deployments
    def test_list_deployments_by_status(
        self, deployment_service, approved_version, db_session
    ):
        """Test listing deployments filtered by status."""
        # Create succeeded deployment
        data1 = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="list-test-1"
        )
        dep1, _ = deployment_service.create_deployment(data1)
        obj1 = db_session.query(
            Deployment
        ).filter_by(id=dep1.id).first()
        obj1.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Create failed deployment
        data2 = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="list-test-2"
        )
        dep2, _ = deployment_service.create_deployment(data2)
        obj2 = db_session.query(
            Deployment
        ).filter_by(id=dep2.id).first()
        obj2.status = DeploymentStatus.FAILED
        db_session.commit()

        # List only succeeded
        succeeded = deployment_service.list_deployments(status="SUCCEEDED")
        succeeded_ids = [d.id for d in succeeded]
        assert dep1.id in succeeded_ids
        assert dep2.id not in succeeded_ids

    def test_list_deployments_by_environment(
        self, deployment_service, approved_version, db_session
    ):
        """Test listing deployments filtered by environment."""
        # Create STAGING deployment
        staging_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="env-filter-staging"
        )
        staging_dep, _ = deployment_service.create_deployment(staging_data)

        # Create succeeded STAGING deployment to enable PRODUCTION
        obj = db_session.query(
            Deployment
        ).filter_by(id=staging_dep.id).first()
        obj.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Create PRODUCTION deployment
        prod_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="PRODUCTION",
            idempotency_key="env-filter-prod"
        )
        prod_dep, _ = deployment_service.create_deployment(prod_data)

        # Filter by environment
        staging_deployments = deployment_service.list_deployments(environment="STAGING")
        staging_ids = [d.id for d in staging_deployments]
        assert staging_dep.id in staging_ids
        assert prod_dep.id not in staging_ids

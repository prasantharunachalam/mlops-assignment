"""
Integration tests for deployment rollback and idempotency.

Tests:
- Rollback creates new deployment pointing to prior version
- Rollback requires prior successful deployment
- Idempotency keys prevent duplicate deployments
- Idempotency works across retries
"""
import pytest
from app.models import DeploymentStatus, Deployment
from app.services import DeploymentService
from app.repositories import DeploymentRepository, ModelRepository
from app.schemas.deployment import DeploymentCreate


class TestRollbackAndIdempotency:
    """Integration tests for rollback and idempotency features."""

    @pytest.fixture
    def deployment_service(self, db_session):
        """Create a DeploymentService instance for testing."""
        deployment_repo = DeploymentRepository(db_session)
        model_repo = ModelRepository(db_session)
        return DeploymentService(deployment_repo, model_repo)

    # Rollback tests
    def test_rollback_to_prior_successful_deployment(
        self, deployment_service, approved_version, sample_model, db_session
    ):
        """Test rolling back to a prior successful deployment."""
        # Create version 1.0.0
        from app.models import ModelVersion
        from tests.conftest import generate_version_id
        version_1 = ModelVersion(
            id=generate_version_id(),
            model_id=sample_model.id,
            version_number="1.0.0",
            framework="sklearn",
            algorithm="RandomForest",
            artifact_uri="s3://models/v1",
            lifecycle_stage="APPROVED"
        )
        db_session.add(version_1)
        db_session.commit()
        db_session.refresh(version_1)

        # Deploy version 1.0.0 to STAGING (succeeded)
        deploy_v1 = DeploymentCreate(
            model_version_id=version_1.id,
            environment="STAGING",
            idempotency_key="rollback-test-v1"
        )
        dep_v1, _ = deployment_service.create_deployment(deploy_v1)
        obj_v1 = db_session.query(
            Deployment
        ).filter_by(id=dep_v1.id).first()
        obj_v1.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Deploy version 2.0.0 to STAGING (succeeded)
        deploy_v2 = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="rollback-test-v2"
        )
        dep_v2, _ = deployment_service.create_deployment(deploy_v2)
        obj_v2 = db_session.query(
            Deployment
        ).filter_by(id=dep_v2.id).first()
        obj_v2.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Rollback deployment v2
        rollback, error = deployment_service.rollback_deployment(dep_v2.id)

        assert error is None
        assert rollback is not None
        assert rollback.model_version_id == version_1.id  # Back to v1
        assert rollback.environment == "STAGING"
        assert rollback.rolled_back_from_id == dep_v2.id
        assert rollback.idempotency_key == f"rollback-{dep_v2.id}"
        assert rollback.status == DeploymentStatus.REQUESTED

    def test_rollback_without_prior_deployment_fails(
        self, deployment_service, approved_version
    ):
        """Test that rollback fails when there's no prior deployment."""
        # Create first deployment (no prior)
        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="first-deployment"
        )
        deployment, _ = deployment_service.create_deployment(deployment_data)

        # Try to rollback
        rollback, error = deployment_service.rollback_deployment(deployment.id)

        assert rollback is None
        assert error == "No prior successful deployment to rollback to"

    def test_rollback_with_only_failed_prior_deployments_fails(
        self, deployment_service, approved_version, db_session
    ):
        """Test rollback fails when all prior deployments failed."""
        # Create first deployment and mark as failed
        dep1_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="failed-dep-1"
        )
        dep1, _ = deployment_service.create_deployment(dep1_data)
        obj1 = db_session.query(
            Deployment
        ).filter_by(id=dep1.id).first()
        obj1.status = DeploymentStatus.FAILED
        db_session.commit()

        # Create second deployment
        dep2_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="current-dep"
        )
        dep2, _ = deployment_service.create_deployment(dep2_data)

        # Try to rollback
        rollback, error = deployment_service.rollback_deployment(dep2.id)

        assert rollback is None
        assert error == "No prior successful deployment to rollback to"

    def test_rollback_to_different_model_version(
        self, deployment_service, sample_model, db_session
    ):
        """Test rollback works when prior deployment used a different model version."""
        from app.models import ModelVersion

        # Create two different versions
        from tests.conftest import generate_version_id
        v1 = ModelVersion(
            id=generate_version_id(),
            model_id=sample_model.id,
            version_number="1.0.0",
            framework="sklearn",
            algorithm="RandomForest",
            artifact_uri="s3://models/v1",
            lifecycle_stage="APPROVED"
        )
        v2 = ModelVersion(
            id=generate_version_id(),
            model_id=sample_model.id,
            version_number="2.0.0",
            framework="tensorflow",
            algorithm="NeuralNet",
            artifact_uri="s3://models/v2",
            lifecycle_stage="APPROVED"
        )
        db_session.add_all([v1, v2])
        db_session.commit()
        db_session.refresh(v1)
        db_session.refresh(v2)

        # Deploy v1 (succeeded)
        dep_v1_data = DeploymentCreate(
            model_version_id=v1.id,
            environment="PRODUCTION",
            idempotency_key="prod-v1"
        )
        dep_v1, _ = deployment_service.create_deployment(dep_v1_data)
        obj_v1 = db_session.query(
            Deployment
        ).filter_by(id=dep_v1.id).first()
        obj_v1.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Deploy v2 (succeeded)
        dep_v2_data = DeploymentCreate(
            model_version_id=v2.id,
            environment="PRODUCTION",
            idempotency_key="prod-v2"
        )
        dep_v2, _ = deployment_service.create_deployment(dep_v2_data)
        obj_v2 = db_session.query(
            Deployment
        ).filter_by(id=dep_v2.id).first()
        obj_v2.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Rollback v2 to v1
        rollback, error = deployment_service.rollback_deployment(dep_v2.id)

        assert error is None
        assert rollback.model_version_id == v1.id
        assert rollback.environment == "PRODUCTION"

    def test_rollback_nonexistent_deployment_fails(self, deployment_service):
        """Test rollback fails for non-existent deployment."""
        rollback, error = deployment_service.rollback_deployment("nonexistent-id")

        assert rollback is None
        assert error == "Deployment not found"

    def test_multiple_rollbacks_create_chain(
        self, deployment_service, sample_model, db_session
    ):
        """Test that multiple rollbacks create a chain of deployments."""
        from app.models import ModelVersion

        # Create three versions
        from tests.conftest import generate_version_id
        versions = []
        for i in range(1, 4):
            v = ModelVersion(
                id=generate_version_id(),
                model_id=sample_model.id,
                version_number=f"{i}.0.0",
                framework="sklearn",
                algorithm="RandomForest",
                artifact_uri=f"s3://models/v{i}",
                lifecycle_stage="APPROVED"
            )
            versions.append(v)
        db_session.add_all(versions)
        db_session.commit()
        for v in versions:
            db_session.refresh(v)

        # Deploy all three versions
        deployments = []
        for i, version in enumerate(versions):
            dep_data = DeploymentCreate(
                model_version_id=version.id,
                environment="STAGING",
                idempotency_key=f"chain-v{i+1}"
            )
            dep, _ = deployment_service.create_deployment(dep_data)
            obj = db_session.query(
                Deployment
            ).filter_by(id=dep.id).first()
            obj.status = DeploymentStatus.SUCCEEDED
            db_session.commit()
            deployments.append(dep)

        # Rollback from v3 to v2
        rollback1, _ = deployment_service.rollback_deployment(deployments[2].id)
        assert rollback1.model_version_id == versions[1].id

        # Mark rollback as succeeded
        obj = db_session.query(
            Deployment
        ).filter_by(id=rollback1.id).first()
        obj.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Rollback from rollback (now at v2) to v1
        rollback2, _ = deployment_service.rollback_deployment(rollback1.id)
        assert rollback2.model_version_id == versions[0].id

    # Idempotency tests
    def test_idempotency_key_prevents_duplicate_deployments(
        self, deployment_service, approved_version, db_session
    ):
        """Test that using the same idempotency key prevents duplicate deployments."""
        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="unique-key-123"
        )

        # First deployment succeeds
        dep1, error1 = deployment_service.create_deployment(deployment_data)
        assert error1 is None
        assert dep1 is not None

        # Second deployment with same key should be prevented by DB unique constraint
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            deployment_service.create_deployment(deployment_data)
            db_session.commit()

        db_session.rollback()

    def test_different_idempotency_keys_allow_multiple_deployments(
        self, deployment_service, approved_version
    ):
        """Test that different idempotency keys allow multiple deployments."""
        # First deployment
        data1 = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="key-1"
        )
        dep1, _ = deployment_service.create_deployment(data1)

        # Second deployment with different key
        data2 = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="key-2"
        )
        dep2, error = deployment_service.create_deployment(data2)

        assert error is None
        assert dep2 is not None
        assert dep1.id != dep2.id
        assert dep1.idempotency_key != dep2.idempotency_key

    def test_rollback_generates_unique_idempotency_key(
        self, deployment_service, sample_model, db_session
    ):
        """Test that rollback generates a unique idempotency key."""
        from app.models import ModelVersion

        # Create two versions
        from tests.conftest import generate_version_id
        v1 = ModelVersion(
            id=generate_version_id(),
            model_id=sample_model.id,
            version_number="1.0.0",
            framework="sklearn",
            algorithm="RF",
            artifact_uri="s3://v1",
            lifecycle_stage="APPROVED"
        )
        v2 = ModelVersion(
            id=generate_version_id(),
            model_id=sample_model.id,
            version_number="2.0.0",
            framework="sklearn",
            algorithm="RF",
            artifact_uri="s3://v2",
            lifecycle_stage="APPROVED"
        )
        db_session.add_all([v1, v2])
        db_session.commit()
        db_session.refresh(v1)
        db_session.refresh(v2)

        # Deploy v1
        dep1_data = DeploymentCreate(
            model_version_id=v1.id,
            environment="STAGING",
            idempotency_key="original-deploy"
        )
        dep1, _ = deployment_service.create_deployment(dep1_data)
        obj1 = db_session.query(
            Deployment
        ).filter_by(id=dep1.id).first()
        obj1.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Deploy v2
        dep2_data = DeploymentCreate(
            model_version_id=v2.id,
            environment="STAGING",
            idempotency_key="updated-deploy"
        )
        dep2, _ = deployment_service.create_deployment(dep2_data)
        obj2 = db_session.query(
            Deployment
        ).filter_by(id=dep2.id).first()
        obj2.status = DeploymentStatus.SUCCEEDED
        db_session.commit()

        # Rollback
        rollback, _ = deployment_service.rollback_deployment(dep2.id)

        assert rollback.idempotency_key == f"rollback-{dep2.id}"
        assert rollback.idempotency_key != dep1.idempotency_key
        assert rollback.idempotency_key != dep2.idempotency_key

    def test_idempotency_key_is_case_sensitive(
        self, deployment_service, approved_version, db_session
    ):
        """Test that idempotency keys are case-sensitive."""
        # Deploy with lowercase key
        data1 = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="mykey"
        )
        dep1, _ = deployment_service.create_deployment(data1)

        # Deploy with uppercase key (should succeed as different key)
        data2 = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="MYKEY"
        )
        dep2, error = deployment_service.create_deployment(data2)

        assert error is None
        assert dep2 is not None
        assert dep1.id != dep2.id

    def test_retry_preserves_original_idempotency_key(
        self, deployment_service, approved_version, db_session
    ):
        """Test that retrying a deployment preserves the original idempotency key."""
        deployment_data = DeploymentCreate(
            model_version_id=approved_version.id,
            environment="STAGING",
            idempotency_key="retry-test-key"
        )
        deployment, _ = deployment_service.create_deployment(deployment_data)

        original_key = deployment.idempotency_key
        original_id = deployment.id

        # Mark as failed
        obj = db_session.query(
            Deployment
        ).filter_by(id=deployment.id).first()
        obj.status = DeploymentStatus.FAILED
        db_session.commit()

        # Retry
        retried, _ = deployment_service.retry_deployment(deployment.id)

        # Same deployment object, same idempotency key
        assert retried.id == original_id
        assert retried.idempotency_key == original_key
        assert retried.attempt_count == 2

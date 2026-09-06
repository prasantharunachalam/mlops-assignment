from typing import Optional, List
from app.models import DeploymentStatus, LifecycleStage
from app.repositories import DeploymentRepository, ModelRepository
from app.schemas.deployment import DeploymentCreate, DeploymentResponse


class DeploymentService:
    MAX_RETRY_ATTEMPTS = 3

    def __init__(self, deployment_repo: DeploymentRepository, model_repo: ModelRepository):
        self.deployment_repo = deployment_repo
        self.model_repo = model_repo

    def create_deployment(
        self, deployment_data: DeploymentCreate
    ) -> tuple[Optional[DeploymentResponse], Optional[str]]:
        """Returns (deployment, error_message)"""
        # Validate model version exists
        version = self.model_repo.get_version(deployment_data.model_version_id)
        if not version:
            return None, "Model version not found"

        # Enforce approval gate for PRODUCTION
        if deployment_data.environment.upper() == "PRODUCTION":
            if version.lifecycle_stage not in [
                LifecycleStage.APPROVED,
                LifecycleStage.STAGING,
                LifecycleStage.PRODUCTION,
            ]:
                return None, f"Cannot deploy {version.lifecycle_stage} version to PRODUCTION"

        # Enforce STAGING before PRODUCTION
        if deployment_data.environment.upper() == "PRODUCTION":
            if version.lifecycle_stage == LifecycleStage.APPROVED:
                # Check if version was deployed to STAGING first
                staging_deployment = self._get_version_staging_deployment(version.id)
                if not staging_deployment:
                    return None, "Version must be deployed to STAGING before PRODUCTION"

        deployment = self.deployment_repo.create_deployment(deployment_data)
        return DeploymentResponse.model_validate(deployment), None

    def get_deployment(self, deployment_id: str) -> Optional[DeploymentResponse]:
        deployment = self.deployment_repo.get_deployment(deployment_id)
        return DeploymentResponse.model_validate(deployment) if deployment else None

    def list_deployments(
        self, status: Optional[str] = None, environment: Optional[str] = None
    ) -> List[DeploymentResponse]:
        deployments = self.deployment_repo.list_deployments(
            status=status, environment=environment
        )
        # Enrich with model and version info
        responses = []
        for d in deployments:
            response = DeploymentResponse.model_validate(d)
            version = self.model_repo.get_version(d.model_version_id)
            if version:
                response.version_number = version.version_number
                model = self.model_repo.get_model(version.model_id)
                if model:
                    response.model_name = model.name
            responses.append(response)
        return responses

    def retry_deployment(
        self, deployment_id: str
    ) -> tuple[Optional[DeploymentResponse], Optional[str]]:
        """Returns (deployment, error_message)"""
        deployment = self.deployment_repo.get_deployment(deployment_id)
        if not deployment:
            return None, "Deployment not found"

        if deployment.status != DeploymentStatus.FAILED:
            return None, "Can only retry FAILED deployments"

        if deployment.attempt_count >= self.MAX_RETRY_ATTEMPTS:
            return None, f"Max retry attempts ({self.MAX_RETRY_ATTEMPTS}) reached"

        updated = self.deployment_repo.increment_attempt(deployment_id)
        return DeploymentResponse.model_validate(updated), None

    def rollback_deployment(
        self, deployment_id: str
    ) -> tuple[Optional[DeploymentResponse], Optional[str]]:
        """Returns (new_deployment, error_message)"""
        current = self.deployment_repo.get_deployment(deployment_id)
        if not current:
            return None, "Deployment not found"

        # Find prior successful deployment
        version = self.model_repo.get_version(current.model_version_id)
        if not version:
            return None, "Model version not found"

        prior = self.deployment_repo.get_latest_succeeded_deployment(
            version.model_id, current.environment, exclude_deployment_id=deployment_id
        )
        if not prior:
            return None, "No prior successful deployment to rollback to"

        # Create new deployment with rollback reference
        rollback_data = DeploymentCreate(
            model_version_id=prior.model_version_id,
            environment=current.environment,
            idempotency_key=f"rollback-{deployment_id}",
        )
        new_deployment = self.deployment_repo.create_deployment(rollback_data)
        new_deployment.rolled_back_from_id = deployment_id
        self.deployment_repo.db.commit()

        return DeploymentResponse.model_validate(new_deployment), None

    def _get_version_staging_deployment(self, version_id: str) -> Optional[object]:
        # Check both uppercase and lowercase staging
        deployments = self.deployment_repo.list_deployments()
        for d in deployments:
            if (d.model_version_id == version_id and
                d.status == DeploymentStatus.SUCCEEDED and
                d.environment.upper() == "STAGING"):
                return d
        return None

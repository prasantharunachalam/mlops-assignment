from typing import Optional, List
from app.models import LifecycleStage
from app.repositories import ModelRepository
from app.schemas.model import ModelCreate, ModelResponse
from app.schemas.model_version import ModelVersionCreate, ModelVersionResponse


class RegistryService:
    # Valid lifecycle stage transitions
    LIFECYCLE_TRANSITIONS = {
        LifecycleStage.DRAFT: [LifecycleStage.VALIDATED],
        LifecycleStage.VALIDATED: [LifecycleStage.APPROVED, LifecycleStage.DRAFT],
        LifecycleStage.APPROVED: [LifecycleStage.STAGING, LifecycleStage.VALIDATED],
        LifecycleStage.STAGING: [LifecycleStage.PRODUCTION, LifecycleStage.APPROVED],
        LifecycleStage.PRODUCTION: [LifecycleStage.ARCHIVED, LifecycleStage.STAGING],
        LifecycleStage.ARCHIVED: [],
    }

    def __init__(self, repo: ModelRepository):
        self.repo = repo

    def create_model(self, model_data: ModelCreate) -> ModelResponse:
        model = self.repo.create_model(model_data)
        return ModelResponse.model_validate(model)

    def get_model(self, model_id: str) -> Optional[ModelResponse]:
        model = self.repo.get_model(model_id)
        return ModelResponse.model_validate(model) if model else None

    def list_models(self, cursor: Optional[str] = None) -> List[ModelResponse]:
        models = self.repo.list_models(cursor=cursor)
        return [ModelResponse.model_validate(m) for m in models]

    def create_version(
        self, model_id: str, version_data: ModelVersionCreate
    ) -> Optional[ModelVersionResponse]:
        # Verify model exists
        model = self.repo.get_model(model_id)
        if not model:
            return None

        version = self.repo.create_version(model_id, version_data)
        return ModelVersionResponse.model_validate(version)

    def get_version(self, version_id: str) -> Optional[ModelVersionResponse]:
        version = self.repo.get_version(version_id)
        return ModelVersionResponse.model_validate(version) if version else None

    def list_versions(self, model_id: str) -> List[ModelVersionResponse]:
        versions = self.repo.list_versions(model_id)
        return [ModelVersionResponse.model_validate(v) for v in versions]

    def promote_lifecycle(
        self, version_id: str, target_stage: LifecycleStage, row_version: int
    ) -> tuple[Optional[ModelVersionResponse], Optional[str]]:
        """Returns (version, error_message)"""
        version = self.repo.get_version(version_id)
        if not version:
            return None, "Version not found"

        # Validate transition
        current_stage = version.lifecycle_stage
        if target_stage not in self.LIFECYCLE_TRANSITIONS.get(current_stage, []):
            return (
                None,
                f"Invalid transition from {current_stage} to {target_stage}",
            )

        # Optimistic locking check
        updated = self.repo.update_lifecycle_stage(version_id, target_stage, row_version)
        if not updated:
            return None, "Conflict: row_version mismatch"

        return ModelVersionResponse.model_validate(updated), None

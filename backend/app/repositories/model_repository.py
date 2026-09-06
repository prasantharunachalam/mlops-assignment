from sqlalchemy.orm import Session
from typing import Optional, List
from app.models import Model, ModelVersion
from app.schemas.model import ModelCreate
from app.schemas.model_version import ModelVersionCreate


class ModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_model(self, model_data: ModelCreate) -> Model:
        from datetime import datetime
        model_id = f"model-{datetime.utcnow().timestamp()}"
        model = Model(id=model_id, **model_data.model_dump())
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_model(self, model_id: str) -> Optional[Model]:
        return self.db.query(Model).filter(Model.id == model_id).first()

    def list_models(self, cursor: Optional[str] = None, limit: int = 50) -> List[Model]:
        query = self.db.query(Model).order_by(Model.created_at.desc())
        if cursor:
            query = query.filter(Model.created_at < cursor)
        return query.limit(limit).all()

    def create_version(self, model_id: str, version_data: ModelVersionCreate) -> ModelVersion:
        from datetime import datetime
        version_id = f"ver-{datetime.utcnow().timestamp()}"
        version = ModelVersion(id=version_id, model_id=model_id, **version_data.model_dump())
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def get_version(self, version_id: str) -> Optional[ModelVersion]:
        return self.db.query(ModelVersion).filter(ModelVersion.id == version_id).first()

    def list_versions(self, model_id: str) -> List[ModelVersion]:
        return (
            self.db.query(ModelVersion)
            .filter(ModelVersion.model_id == model_id)
            .order_by(ModelVersion.created_at.desc())
            .all()
        )

    def update_lifecycle_stage(
        self, version_id: str, target_stage: str, expected_row_version: int
    ) -> Optional[ModelVersion]:
        version = self.get_version(version_id)
        if not version or version.row_version != expected_row_version:
            return None

        version.lifecycle_stage = target_stage
        version.row_version += 1
        self.db.commit()
        self.db.refresh(version)
        return version

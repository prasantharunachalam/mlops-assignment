from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Optional, List
from app.models import Model, ModelVersion
from app.schemas.model import ModelCreate
from app.schemas.model_version import ModelVersionCreate
import uuid


class ModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_model(self, model_data: ModelCreate) -> Model:
        model_id = f"model-{uuid.uuid4()}"
        model = Model(id=model_id, **model_data.model_dump())
        self.db.add(model)
        try:
            self.db.commit()
            self.db.refresh(model)
            return model
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Model creation failed due to constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f"Database error during model creation: {str(e)}")

    def get_model(self, model_id: str) -> Optional[Model]:
        return self.db.query(Model).filter(Model.id == model_id).first()

    def list_models(self, cursor: Optional[str] = None, limit: int = 50) -> List[Model]:
        query = self.db.query(Model).order_by(Model.created_at.desc())
        if cursor:
            query = query.filter(Model.created_at < cursor)
        return query.limit(limit).all()

    def create_version(self, model_id: str, version_data: ModelVersionCreate) -> ModelVersion:
        version_id = f"ver-{uuid.uuid4()}"
        version = ModelVersion(id=version_id, model_id=model_id, **version_data.model_dump())
        self.db.add(version)
        try:
            self.db.commit()
            self.db.refresh(version)
            return version
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Version creation failed due to constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f"Database error during version creation: {str(e)}")

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
        try:
            self.db.commit()
            self.db.refresh(version)
            return version
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f"Database error during lifecycle update: {str(e)}")

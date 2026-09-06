from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Optional, List
from datetime import datetime
import uuid
from app.models import Deployment, DeploymentStatus, ModelVersion, Model
from app.schemas.deployment import DeploymentCreate


class DeploymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_deployment(self, deployment_data: DeploymentCreate, correlation_id: Optional[str] = None) -> Deployment:
        # Check for existing idempotency key
        existing = self.get_by_idempotency_key(deployment_data.idempotency_key)
        if existing:
            return existing

        deployment = Deployment(
            id=f"dep-{uuid.uuid4()}",
            correlation_id=correlation_id,
            **deployment_data.model_dump(),
        )
        self.db.add(deployment)
        try:
            self.db.commit()
            self.db.refresh(deployment)
            return deployment
        except IntegrityError as e:
            self.db.rollback()
            # Check again for duplicate idempotency key (race condition)
            existing = self.get_by_idempotency_key(deployment_data.idempotency_key)
            if existing:
                return existing
            raise ValueError(f"Deployment creation failed due to constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f"Database error during deployment creation: {str(e)}")

    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        return self.db.query(Deployment).filter(Deployment.id == deployment_id).first()

    def get_by_idempotency_key(self, key: str) -> Optional[Deployment]:
        return self.db.query(Deployment).filter(Deployment.idempotency_key == key).first()

    def list_deployments(
        self, status: Optional[str] = None, environment: Optional[str] = None, limit: int = 50
    ) -> List[Deployment]:
        # Use joinedload to eagerly fetch related ModelVersion and Model (prevents N+1 queries)
        query = (
            self.db.query(Deployment)
            .options(
                joinedload(Deployment.model_version).joinedload(ModelVersion.model)
            )
            .order_by(Deployment.requested_at.desc())
        )
        if status:
            query = query.filter(Deployment.status == status)
        if environment:
            query = query.filter(Deployment.environment == environment)
        return query.limit(limit).all()

    def update_status(
        self, deployment_id: str, status: DeploymentStatus, failure_reason: Optional[str] = None
    ) -> Optional[Deployment]:
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None

        deployment.status = status
        if status in [DeploymentStatus.SUCCEEDED, DeploymentStatus.FAILED]:
            deployment.completed_at = datetime.utcnow()
        if failure_reason:
            deployment.failure_reason = failure_reason

        try:
            self.db.commit()
            self.db.refresh(deployment)
            return deployment
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f"Database error during status update: {str(e)}")

    def increment_attempt(self, deployment_id: str) -> Optional[Deployment]:
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None

        deployment.attempt_count += 1
        deployment.status = DeploymentStatus.REQUESTED
        try:
            self.db.commit()
            self.db.refresh(deployment)
            return deployment
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f"Database error during attempt increment: {str(e)}")

    def get_latest_succeeded_deployment(
        self, model_id: str, environment: str, exclude_deployment_id: Optional[str] = None
    ) -> Optional[Deployment]:
        from app.models import ModelVersion
        query = (
            self.db.query(Deployment)
            .join(ModelVersion, Deployment.model_version_id == ModelVersion.id)
            .filter(
                and_(
                    ModelVersion.model_id == model_id,
                    Deployment.environment == environment,
                    Deployment.status == DeploymentStatus.SUCCEEDED,
                )
            )
        )
        if exclude_deployment_id:
            query = query.filter(Deployment.id != exclude_deployment_id)

        return query.order_by(Deployment.completed_at.desc()).first()

    def get_requested_deployments(self, limit: int = 10) -> List[Deployment]:
        return (
            self.db.query(Deployment)
            .filter(Deployment.status == DeploymentStatus.REQUESTED)
            .order_by(Deployment.requested_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
            .all()
        )

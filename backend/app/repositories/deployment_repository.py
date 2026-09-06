from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime
from app.models import Deployment, DeploymentStatus
from app.schemas.deployment import DeploymentCreate


class DeploymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_deployment(self, deployment_data: DeploymentCreate) -> Deployment:
        # Check for existing idempotency key
        existing = self.get_by_idempotency_key(deployment_data.idempotency_key)
        if existing:
            return existing

        deployment = Deployment(
            id=f"dep-{datetime.utcnow().timestamp()}",
            **deployment_data.model_dump(),
        )
        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)
        return deployment

    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        return self.db.query(Deployment).filter(Deployment.id == deployment_id).first()

    def get_by_idempotency_key(self, key: str) -> Optional[Deployment]:
        return self.db.query(Deployment).filter(Deployment.idempotency_key == key).first()

    def list_deployments(
        self, status: Optional[str] = None, environment: Optional[str] = None, limit: int = 50
    ) -> List[Deployment]:
        query = self.db.query(Deployment).order_by(Deployment.requested_at.desc())
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

        self.db.commit()
        self.db.refresh(deployment)
        return deployment

    def increment_attempt(self, deployment_id: str) -> Optional[Deployment]:
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None

        deployment.attempt_count += 1
        deployment.status = DeploymentStatus.REQUESTED
        self.db.commit()
        self.db.refresh(deployment)
        return deployment

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

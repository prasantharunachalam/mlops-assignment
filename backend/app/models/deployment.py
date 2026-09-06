from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class DeploymentStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    DEPLOYING = "DEPLOYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(String, primary_key=True)
    model_version_id = Column(String, ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False)
    environment = Column(String, nullable=False)
    status = Column(Enum(DeploymentStatus), default=DeploymentStatus.REQUESTED, nullable=False)
    idempotency_key = Column(String, nullable=False, unique=True)
    correlation_id = Column(String, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    rolled_back_from_id = Column(String, ForeignKey("deployments.id"))
    attempt_count = Column(Integer, default=1, nullable=False)
    failure_reason = Column(String)

    model_version = relationship("ModelVersion", back_populates="deployments")
    rolled_back_from = relationship("Deployment", remote_side=[id], uselist=False)

    __table_args__ = (
        Index("ix_deployments_status_created", "status", "requested_at"),
        Index("ix_deployments_environment", "environment"),
        Index("ix_deployments_model_version_id", "model_version_id"),
        Index("ix_deployments_correlation_id", "correlation_id"),
        UniqueConstraint("idempotency_key", name="uq_deployments_idempotency_key"),
    )

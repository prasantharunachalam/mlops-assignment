from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class LifecycleStage(str, enum.Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String, primary_key=True)
    model_id = Column(String, ForeignKey("models.id", ondelete="RESTRICT"), nullable=False)
    version_number = Column(String, nullable=False)
    framework = Column(String, nullable=False)
    algorithm = Column(String)
    artifact_uri = Column(String, nullable=False)
    training_data_ref = Column(String)
    tags = Column(JSON, default=dict)
    lifecycle_stage = Column(Enum(LifecycleStage), default=LifecycleStage.DRAFT, nullable=False)
    row_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    model = relationship("Model", back_populates="versions")
    deployments = relationship("Deployment", back_populates="model_version")
    metrics = relationship("MetricSnapshot", back_populates="model_version")

    __table_args__ = (
        Index("ix_model_versions_model_id", "model_id"),
        Index("ix_model_versions_lifecycle_stage", "lifecycle_stage"),
    )

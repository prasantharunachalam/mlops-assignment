from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id = Column(String, primary_key=True)
    model_version_id = Column(String, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    latency_ms = Column(Float)
    throughput_rps = Column(Float)
    error_rate = Column(Float)
    quality_score = Column(Float)
    drift_score = Column(Float)
    availability = Column(Float)

    model_version = relationship("ModelVersion", back_populates="metrics")

    __table_args__ = (
        Index("ix_metrics_model_version_captured", "model_version_id", "captured_at"),
        Index("ix_metrics_captured_at", "captured_at"),
    )

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class MetricSnapshotCreate(BaseModel):
    model_version_id: str = Field(..., min_length=1)
    latency_ms: Optional[float] = None
    throughput_rps: Optional[float] = None
    error_rate: Optional[float] = None
    quality_score: Optional[float] = None
    drift_score: Optional[float] = None
    availability: Optional[float] = None


class MetricSnapshotResponse(BaseModel):
    id: str
    model_version_id: str
    captured_at: datetime
    latency_ms: Optional[float]
    throughput_rps: Optional[float]
    error_rate: Optional[float]
    quality_score: Optional[float]
    drift_score: Optional[float]
    availability: Optional[float]

    class Config:
        from_attributes = True


class MetricListResponse(BaseModel):
    items: list[MetricSnapshotResponse]

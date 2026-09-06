from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.models.deployment import DeploymentStatus


class DeploymentCreate(BaseModel):
    model_version_id: str = Field(..., min_length=1)
    environment: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=1, description="Client-generated UUID")


class DeploymentResponse(BaseModel):
    id: str
    model_version_id: str
    environment: str
    status: DeploymentStatus
    idempotency_key: str
    correlation_id: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime]
    rolled_back_from_id: Optional[str]
    attempt_count: int
    failure_reason: Optional[str]
    # Computed fields for display
    model_name: Optional[str] = None
    version_number: Optional[str] = None

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    items: list[DeploymentResponse]
    next_cursor: Optional[str] = None

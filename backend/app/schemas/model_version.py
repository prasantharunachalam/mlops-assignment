from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.model_version import LifecycleStage


class ModelVersionCreate(BaseModel):
    version_number: str = Field(..., min_length=1)
    framework: str = Field(..., min_length=1)
    algorithm: Optional[str] = None
    artifact_uri: str = Field(..., min_length=1)
    training_data_ref: Optional[str] = None
    tags: Dict[str, Any] = Field(default_factory=dict)


class ModelVersionResponse(BaseModel):
    id: str
    model_id: str
    version_number: str
    framework: str
    algorithm: Optional[str]
    artifact_uri: str
    training_data_ref: Optional[str]
    tags: Dict[str, Any]
    lifecycle_stage: LifecycleStage
    row_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LifecyclePromoteRequest(BaseModel):
    target_stage: LifecycleStage
    row_version: int = Field(..., description="Current row_version for optimistic locking")


class ModelVersionListResponse(BaseModel):
    items: list[ModelVersionResponse]
    next_cursor: Optional[str] = None

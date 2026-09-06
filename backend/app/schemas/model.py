from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    owner: str = Field(..., min_length=1)


class ModelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner: str
    created_at: datetime

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    items: list[ModelResponse]
    next_cursor: Optional[str] = None

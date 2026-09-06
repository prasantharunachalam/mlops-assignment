from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    code: str
    message: str
    correlation_id: str
    details: Optional[Dict[str, Any]] = None

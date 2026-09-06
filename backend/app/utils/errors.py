from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.schemas.error import ErrorResponse
from app.utils.logging import get_correlation_id


class MLOpsException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


def create_error_response(status_code: int, code: str, message: str, details: dict = None):
    error = ErrorResponse(
        code=code,
        message=message,
        correlation_id=get_correlation_id(),
        details=details,
    )
    return JSONResponse(status_code=status_code, content={"error": error.model_dump()})


def validation_error(message: str, details: dict = None):
    return create_error_response(400, "VALIDATION_ERROR", message, details)


def not_found_error(message: str):
    return create_error_response(404, "NOT_FOUND", message)


def conflict_error(message: str, details: dict = None):
    return create_error_response(409, "CONFLICT", message, details)


def internal_error(message: str = "Internal server error"):
    return create_error_response(500, "INTERNAL_ERROR", message)

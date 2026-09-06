from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.repositories import ModelRepository
from app.services import RegistryService
from app.schemas.model import ModelCreate, ModelResponse, ModelListResponse
from app.schemas.model_version import (
    ModelVersionCreate,
    ModelVersionResponse,
    LifecyclePromoteRequest,
    ModelVersionListResponse,
)
from app.utils.errors import not_found_error, conflict_error

router = APIRouter()


def get_registry_service(db: Session = Depends(get_db)) -> RegistryService:
    return RegistryService(ModelRepository(db))


@router.post("/models", response_model=ModelResponse, status_code=201)
def create_model(
    model_data: ModelCreate,
    service: RegistryService = Depends(get_registry_service),
):
    return service.create_model(model_data)


@router.get("/models", response_model=ModelListResponse)
def list_models(
    cursor: Optional[str] = None,
    service: RegistryService = Depends(get_registry_service),
):
    models = service.list_models(cursor=cursor)
    return ModelListResponse(items=models)


@router.get("/models/{model_id}", response_model=ModelResponse)
def get_model(model_id: str, service: RegistryService = Depends(get_registry_service)):
    model = service.get_model(model_id)
    if not model:
        return not_found_error(f"Model {model_id} not found")
    return model


@router.post("/models/{model_id}/versions", response_model=ModelVersionResponse, status_code=201)
def create_version(
    model_id: str,
    version_data: ModelVersionCreate,
    service: RegistryService = Depends(get_registry_service),
):
    version = service.create_version(model_id, version_data)
    if not version:
        return not_found_error(f"Model {model_id} not found")
    return version


@router.get("/models/{model_id}/versions", response_model=ModelVersionListResponse)
def list_versions(
    model_id: str,
    service: RegistryService = Depends(get_registry_service),
):
    versions = service.list_versions(model_id)
    return ModelVersionListResponse(items=versions)


@router.patch("/models/{model_id}/versions/{version_id}/lifecycle", response_model=ModelVersionResponse)
def promote_lifecycle(
    model_id: str,
    version_id: str,
    request: LifecyclePromoteRequest,
    service: RegistryService = Depends(get_registry_service),
):
    version, error = service.promote_lifecycle(
        version_id, request.target_stage, request.row_version
    )
    if error:
        if "not found" in error.lower():
            return not_found_error(error)
        return conflict_error(error)
    return version

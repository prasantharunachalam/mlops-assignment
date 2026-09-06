from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.repositories import DeploymentRepository, ModelRepository
from app.services import DeploymentService
from app.schemas.deployment import DeploymentCreate, DeploymentResponse, DeploymentListResponse
from app.utils.errors import not_found_error, conflict_error

router = APIRouter()


def get_deployment_service(db: Session = Depends(get_db)) -> DeploymentService:
    return DeploymentService(DeploymentRepository(db), ModelRepository(db))


@router.post("/deployments", response_model=DeploymentResponse, status_code=202)
def create_deployment(
    deployment_data: DeploymentCreate,
    service: DeploymentService = Depends(get_deployment_service),
):
    deployment, error = service.create_deployment(deployment_data)
    if error:
        if "not found" in error.lower():
            return not_found_error(error)
        return conflict_error(error)
    return deployment


@router.get("/deployments", response_model=DeploymentListResponse)
def list_deployments(
    status: Optional[str] = None,
    environment: Optional[str] = None,
    service: DeploymentService = Depends(get_deployment_service),
):
    deployments = service.list_deployments(status=status, environment=environment)
    return DeploymentListResponse(items=deployments)


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(
    deployment_id: str,
    service: DeploymentService = Depends(get_deployment_service),
):
    deployment = service.get_deployment(deployment_id)
    if not deployment:
        return not_found_error(f"Deployment {deployment_id} not found")
    return deployment


@router.post("/deployments/{deployment_id}/retry", response_model=DeploymentResponse)
def retry_deployment(
    deployment_id: str,
    service: DeploymentService = Depends(get_deployment_service),
):
    deployment, error = service.retry_deployment(deployment_id)
    if error:
        if "not found" in error.lower():
            return not_found_error(error)
        return conflict_error(error)
    return deployment


@router.post("/deployments/{deployment_id}/rollback", response_model=DeploymentResponse, status_code=202)
def rollback_deployment(
    deployment_id: str,
    service: DeploymentService = Depends(get_deployment_service),
):
    deployment, error = service.rollback_deployment(deployment_id)
    if error:
        if "not found" in error.lower():
            return not_found_error(error)
        return conflict_error(error)
    return deployment

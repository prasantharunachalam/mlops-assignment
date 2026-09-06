from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.repositories import MetricRepository
from app.services import MonitoringService
from app.schemas.metric import MetricSnapshotCreate, MetricSnapshotResponse, MetricListResponse

router = APIRouter()


def get_monitoring_service(db: Session = Depends(get_db)) -> MonitoringService:
    return MonitoringService(MetricRepository(db))


@router.post("/metrics", response_model=MetricSnapshotResponse, status_code=201)
def ingest_metric(
    metric_data: MetricSnapshotCreate,
    service: MonitoringService = Depends(get_monitoring_service),
):
    return service.ingest_metric(metric_data)


@router.get("/models/{model_id}/versions/{version_id}/metrics", response_model=MetricListResponse)
def get_metrics(
    model_id: str,
    version_id: str,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    service: MonitoringService = Depends(get_monitoring_service),
):
    metrics = service.get_metrics(version_id, start_time, end_time)
    return MetricListResponse(items=metrics)

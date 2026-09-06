from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import DeploymentStatus

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check worker health by looking for recent deployment processing
    # Worker is healthy if there are no stuck REQUESTED deployments older than 5 minutes
    worker_status = "healthy"
    try:
        from datetime import datetime, timedelta
        from app.models import Deployment

        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        stuck_deployments = db.query(Deployment).filter(
            Deployment.status == DeploymentStatus.REQUESTED,
            Deployment.requested_at < five_minutes_ago
        ).count()

        if stuck_deployments > 0:
            worker_status = f"degraded: {stuck_deployments} stuck deployments"
    except Exception as e:
        worker_status = f"unknown: {str(e)}"

    overall_status = "healthy"
    if db_status != "healthy" or "degraded" in worker_status or "unknown" in worker_status:
        overall_status = "degraded"
    if db_status != "healthy" and "unhealthy" in db_status:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "database": db_status,
        "worker": worker_status,
    }

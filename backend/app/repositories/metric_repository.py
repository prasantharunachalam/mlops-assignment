from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
from datetime import datetime
import uuid
from app.models import MetricSnapshot
from app.schemas.metric import MetricSnapshotCreate


class MetricRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_metric(self, metric_data: MetricSnapshotCreate) -> MetricSnapshot:
        metric = MetricSnapshot(
            id=f"metric-{uuid.uuid4()}",
            **metric_data.model_dump(),
        )
        self.db.add(metric)
        try:
            self.db.commit()
            self.db.refresh(metric)
            return metric
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Metric creation failed due to constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f"Database error during metric creation: {str(e)}")

    def get_metrics(
        self,
        model_version_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[MetricSnapshot]:
        return (
            self.db.query(MetricSnapshot)
            .filter(
                MetricSnapshot.model_version_id == model_version_id,
                MetricSnapshot.captured_at >= start_time,
                MetricSnapshot.captured_at <= end_time,
            )
            .order_by(MetricSnapshot.captured_at.desc())
            .all()
        )

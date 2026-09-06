from typing import List
from datetime import datetime
from app.repositories import MetricRepository
from app.schemas.metric import MetricSnapshotCreate, MetricSnapshotResponse


class MonitoringService:
    def __init__(self, repo: MetricRepository):
        self.repo = repo

    def ingest_metric(self, metric_data: MetricSnapshotCreate) -> MetricSnapshotResponse:
        metric = self.repo.create_metric(metric_data)
        return MetricSnapshotResponse.model_validate(metric)

    def get_metrics(
        self,
        model_version_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[MetricSnapshotResponse]:
        metrics = self.repo.get_metrics(model_version_id, start_time, end_time)
        return [MetricSnapshotResponse.model_validate(m) for m in metrics]

export interface MetricSnapshot {
  id: string;
  model_version_id: string;
  captured_at: string;
  latency_ms?: number;
  throughput_rps?: number;
  error_rate?: number;
  quality_score?: number;
  drift_score?: number;
  availability?: number;
}

export interface MetricSnapshotCreate {
  model_version_id: string;
  latency_ms?: number;
  throughput_rps?: number;
  error_rate?: number;
  quality_score?: number;
  drift_score?: number;
  availability?: number;
}

export interface MetricListResponse {
  items: MetricSnapshot[];
}

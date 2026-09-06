import { DeploymentStatus } from './deployment-status.enum';

export interface Deployment {
  id: string;
  model_version_id: string;
  environment: string;
  status: DeploymentStatus;
  idempotency_key: string;
  requested_at: string;
  completed_at?: string;
  rolled_back_from_id?: string;
  attempt_count: number;
  failure_reason?: string;
}

export interface DeploymentCreate {
  model_version_id: string;
  environment: string;
  idempotency_key: string;
}

export interface DeploymentListResponse {
  items: Deployment[];
}

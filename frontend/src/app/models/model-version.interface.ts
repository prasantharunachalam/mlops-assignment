import { LifecycleStage } from './lifecycle-stage.enum';

export interface ModelVersion {
  id: string;
  model_id: string;
  version_number: string;
  framework: string;
  algorithm?: string;
  artifact_uri: string;
  training_data_ref?: string;
  tags: { [key: string]: any };
  lifecycle_stage: LifecycleStage;
  row_version: number;
  created_at: string;
  updated_at: string;
}

export interface ModelVersionCreate {
  version_number: string;
  framework: string;
  algorithm?: string;
  artifact_uri: string;
  training_data_ref?: string;
  tags?: { [key: string]: any };
}

export interface LifecyclePromoteRequest {
  target_stage: LifecycleStage;
  row_version: number;
}

export interface ModelVersionListResponse {
  items: ModelVersion[];
  next_cursor?: string;
}

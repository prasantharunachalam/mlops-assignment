import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Model,
  ModelCreate,
  ModelListResponse,
  ModelVersion,
  ModelVersionCreate,
  ModelVersionListResponse,
  LifecyclePromoteRequest
} from '../models';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ModelService {
  private apiUrl = `${environment.apiUrl}/api/v1`;

  constructor(private http: HttpClient) {}

  // Model operations
  createModel(model: ModelCreate): Observable<Model> {
    return this.http.post<Model>(`${this.apiUrl}/models`, model);
  }

  listModels(cursor?: string): Observable<ModelListResponse> {
    let params = new HttpParams();
    if (cursor) {
      params = params.set('cursor', cursor);
    }
    return this.http.get<ModelListResponse>(`${this.apiUrl}/models`, { params });
  }

  getModel(modelId: string): Observable<Model> {
    return this.http.get<Model>(`${this.apiUrl}/models/${modelId}`);
  }

  // Model version operations
  createVersion(modelId: string, version: ModelVersionCreate): Observable<ModelVersion> {
    return this.http.post<ModelVersion>(
      `${this.apiUrl}/models/${modelId}/versions`,
      version
    );
  }

  listVersions(modelId: string): Observable<ModelVersionListResponse> {
    return this.http.get<ModelVersionListResponse>(
      `${this.apiUrl}/models/${modelId}/versions`
    );
  }

  promoteLifecycle(
    modelId: string,
    versionId: string,
    request: LifecyclePromoteRequest
  ): Observable<ModelVersion> {
    return this.http.patch<ModelVersion>(
      `${this.apiUrl}/models/${modelId}/versions/${versionId}/lifecycle`,
      request
    );
  }
}

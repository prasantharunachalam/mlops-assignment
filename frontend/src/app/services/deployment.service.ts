import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Deployment, DeploymentCreate, DeploymentListResponse } from '../models';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class DeploymentService {
  private apiUrl = `${environment.apiUrl}/api/v1`;

  constructor(private http: HttpClient) {}

  createDeployment(deployment: DeploymentCreate): Observable<Deployment> {
    return this.http.post<Deployment>(`${this.apiUrl}/deployments`, deployment);
  }

  listDeployments(status?: string, environment?: string): Observable<DeploymentListResponse> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }
    if (environment) {
      params = params.set('environment', environment);
    }
    return this.http.get<DeploymentListResponse>(`${this.apiUrl}/deployments`, { params });
  }

  getDeployment(deploymentId: string): Observable<Deployment> {
    return this.http.get<Deployment>(`${this.apiUrl}/deployments/${deploymentId}`);
  }

  retryDeployment(deploymentId: string): Observable<Deployment> {
    return this.http.post<Deployment>(
      `${this.apiUrl}/deployments/${deploymentId}/retry`,
      {}
    );
  }

  rollbackDeployment(deploymentId: string): Observable<Deployment> {
    return this.http.post<Deployment>(
      `${this.apiUrl}/deployments/${deploymentId}/rollback`,
      {}
    );
  }
}

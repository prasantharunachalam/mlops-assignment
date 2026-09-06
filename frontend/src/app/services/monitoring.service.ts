import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { MetricSnapshot, MetricSnapshotCreate, MetricListResponse } from '../models';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class MonitoringService {
  private apiUrl = `${environment.apiUrl}/api/v1`;

  constructor(private http: HttpClient) {}

  ingestMetric(metric: MetricSnapshotCreate): Observable<MetricSnapshot> {
    return this.http.post<MetricSnapshot>(`${this.apiUrl}/metrics`, metric);
  }

  getMetrics(
    modelId: string,
    versionId: string,
    startTime: string,
    endTime: string
  ): Observable<MetricListResponse> {
    let params = new HttpParams()
      .set('start_time', startTime)
      .set('end_time', endTime);

    return this.http.get<MetricListResponse>(
      `${this.apiUrl}/monitoring/models/${modelId}/versions/${versionId}/metrics`,
      { params }
    );
  }
}

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { MonitoringService } from './monitoring.service';
import { MetricSnapshot, MetricSnapshotCreate } from '../models';
import { environment } from '../../environments/environment';

describe('MonitoringService', () => {
  let service: MonitoringService;
  let httpMock: HttpTestingController;
  const apiUrl = `${environment.apiUrl}/api/v1`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [MonitoringService]
    });
    service = TestBed.inject(MonitoringService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('ingestMetric', () => {
    it('should ingest a metric via POST request', () => {
      const metricCreate: MetricSnapshotCreate = {
        model_version_id: 'ver-123',
        latency_p50_ms: 45.2,
        latency_p95_ms: 120.5,
        latency_p99_ms: 250.0,
        throughput_rps: 150.0,
        error_rate: 0.005,
        drift_score: 0.12,
        data_quality_score: 0.98,
        model_availability: 0.999
      };

      const mockResponse: MetricSnapshot = {
        id: 'metric-456',
        ...metricCreate,
        captured_at: new Date().toISOString()
      };

      service.ingestMetric(metricCreate).subscribe(metric => {
        expect(metric).toEqual(mockResponse);
        expect(metric.id).toBe('metric-456');
        expect(metric.throughput_rps).toBe(150.0);
      });

      const req = httpMock.expectOne(`${apiUrl}/metrics`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(metricCreate);
      req.flush(mockResponse);
    });

    it('should handle validation errors (422)', () => {
      const invalidMetric: MetricSnapshotCreate = {
        model_version_id: '',
        latency_p50_ms: -10,
        latency_p95_ms: 0,
        latency_p99_ms: 0,
        throughput_rps: -5,
        error_rate: 1.5,
        drift_score: 0,
        data_quality_score: 0,
        model_availability: 0
      };

      service.ingestMetric(invalidMetric).subscribe(
        () => fail('should have failed with 422 error'),
        error => {
          expect(error.status).toBe(422);
        }
      );

      const req = httpMock.expectOne(`${apiUrl}/metrics`);
      req.flush({ detail: 'Validation error' }, { status: 422, statusText: 'Unprocessable Entity' });
    });
  });

  describe('getMetrics', () => {
    it('should get metrics with time range filters', () => {
      const modelId = 'model-123';
      const versionId = 'ver-456';
      const startTime = '2024-01-01T00:00:00Z';
      const endTime = '2024-01-02T00:00:00Z';

      const mockResponse = {
        items: [
          {
            id: 'metric-1',
            model_version_id: versionId,
            captured_at: '2024-01-01T12:00:00Z',
            latency_p50_ms: 50.0,
            latency_p95_ms: 100.0,
            latency_p99_ms: 200.0,
            throughput_rps: 100.0,
            error_rate: 0.01,
            drift_score: 0.05,
            data_quality_score: 0.95,
            model_availability: 0.99
          },
          {
            id: 'metric-2',
            model_version_id: versionId,
            captured_at: '2024-01-01T18:00:00Z',
            latency_p50_ms: 55.0,
            latency_p95_ms: 110.0,
            latency_p99_ms: 220.0,
            throughput_rps: 95.0,
            error_rate: 0.015,
            drift_score: 0.08,
            data_quality_score: 0.93,
            model_availability: 0.98
          }
        ],
        next_cursor: null
      };

      service.getMetrics(modelId, versionId, startTime, endTime).subscribe(response => {
        expect(response.items.length).toBe(2);
        expect(response.items[0].model_version_id).toBe(versionId);
        expect(response.items[1].latency_p50_ms).toBe(55.0);
      });

      const req = httpMock.expectOne(
        `${apiUrl}/monitoring/models/${modelId}/versions/${versionId}/metrics?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('start_time')).toBe(startTime);
      expect(req.request.params.get('end_time')).toBe(endTime);
      req.flush(mockResponse);
    });

    it('should return empty list when no metrics found', () => {
      const modelId = 'model-new';
      const versionId = 'ver-new';
      const startTime = '2024-01-01T00:00:00Z';
      const endTime = '2024-01-02T00:00:00Z';

      const mockResponse = {
        items: [],
        next_cursor: null
      };

      service.getMetrics(modelId, versionId, startTime, endTime).subscribe(response => {
        expect(response.items.length).toBe(0);
        expect(response.next_cursor).toBeNull();
      });

      const req = httpMock.expectOne(
        `${apiUrl}/monitoring/models/${modelId}/versions/${versionId}/metrics?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`
      );
      req.flush(mockResponse);
    });

    it('should handle invalid version ID (404)', () => {
      const modelId = 'model-123';
      const versionId = 'ver-nonexistent';
      const startTime = '2024-01-01T00:00:00Z';
      const endTime = '2024-01-02T00:00:00Z';

      service.getMetrics(modelId, versionId, startTime, endTime).subscribe(
        () => fail('should have failed with 404 error'),
        error => {
          expect(error.status).toBe(404);
        }
      );

      const req = httpMock.expectOne(
        `${apiUrl}/monitoring/models/${modelId}/versions/${versionId}/metrics?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`
      );
      req.flush({ detail: 'Model version not found' }, { status: 404, statusText: 'Not Found' });
    });

    it('should handle time range validation errors (400)', () => {
      const modelId = 'model-123';
      const versionId = 'ver-456';
      const startTime = '2024-01-02T00:00:00Z';
      const endTime = '2024-01-01T00:00:00Z';

      service.getMetrics(modelId, versionId, startTime, endTime).subscribe(
        () => fail('should have failed with 400 error'),
        error => {
          expect(error.status).toBe(400);
        }
      );

      const req = httpMock.expectOne(
        `${apiUrl}/monitoring/models/${modelId}/versions/${versionId}/metrics?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`
      );
      req.flush({ detail: 'Invalid time range: start_time must be before end_time' }, { status: 400, statusText: 'Bad Request' });
    });
  });
});

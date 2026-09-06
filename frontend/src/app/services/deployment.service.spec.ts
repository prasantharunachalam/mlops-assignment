import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { DeploymentService } from './deployment.service';
import { Deployment, DeploymentCreate, DeploymentStatus } from '../models';
import { environment } from '../../environments/environment';

describe('DeploymentService', () => {
  let service: DeploymentService;
  let httpMock: HttpTestingController;
  const apiUrl = `${environment.apiUrl}/api/v1`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [DeploymentService]
    });
    service = TestBed.inject(DeploymentService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('createDeployment', () => {
    it('should create a deployment via POST request', () => {
      const deploymentCreate: DeploymentCreate = {
        model_version_id: 'ver-123',
        environment: 'staging',
        idempotency_key: 'uuid-abc-123'
      };

      const mockResponse: Deployment = {
        id: 'dep-456',
        ...deploymentCreate,
        status: DeploymentStatus.REQUESTED,
        requested_at: new Date().toISOString(),
        completed_at: null,
        rolled_back_from_id: null,
        attempt_count: 0,
        failure_reason: null,
        model_name: 'test-model',
        version_number: '1.0.0'
      };

      service.createDeployment(deploymentCreate).subscribe(deployment => {
        expect(deployment).toEqual(mockResponse);
        expect(deployment.id).toBe('dep-456');
        expect(deployment.status).toBe(DeploymentStatus.REQUESTED);
      });

      const req = httpMock.expectOne(`${apiUrl}/deployments`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(deploymentCreate);
      req.flush(mockResponse);
    });

    it('should handle idempotency conflict (409)', () => {
      const deploymentCreate: DeploymentCreate = {
        model_version_id: 'ver-123',
        environment: 'production',
        idempotency_key: 'duplicate-key'
      };

      service.createDeployment(deploymentCreate).subscribe(
        () => fail('should have failed with 409 error'),
        error => {
          expect(error.status).toBe(409);
        }
      );

      const req = httpMock.expectOne(`${apiUrl}/deployments`);
      req.flush({ detail: 'Duplicate idempotency key' }, { status: 409, statusText: 'Conflict' });
    });
  });

  describe('listDeployments', () => {
    it('should list all deployments without filters', () => {
      const mockResponse = {
        items: [
          {
            id: 'dep-1',
            model_version_id: 'ver-1',
            environment: 'staging',
            status: DeploymentStatus.SUCCEEDED,
            idempotency_key: 'key-1',
            requested_at: '2024-01-01',
            completed_at: '2024-01-01',
            rolled_back_from_id: null,
            attempt_count: 1,
            failure_reason: null,
            model_name: 'model-1',
            version_number: '1.0.0'
          }
        ],
        next_cursor: null
      };

      service.listDeployments().subscribe(response => {
        expect(response.items.length).toBe(1);
        expect(response.items[0].status).toBe(DeploymentStatus.SUCCEEDED);
      });

      const req = httpMock.expectOne(`${apiUrl}/deployments`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.keys().length).toBe(0);
      req.flush(mockResponse);
    });

    it('should list deployments filtered by status', () => {
      const status = 'FAILED';
      const mockResponse = {
        items: [],
        next_cursor: null
      };

      service.listDeployments(status).subscribe();

      const req = httpMock.expectOne(`${apiUrl}/deployments?status=${status}`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('status')).toBe(status);
      req.flush(mockResponse);
    });

    it('should list deployments filtered by environment', () => {
      const env = 'production';
      const mockResponse = {
        items: [],
        next_cursor: null
      };

      service.listDeployments(undefined, env).subscribe();

      const req = httpMock.expectOne(`${apiUrl}/deployments?environment=${env}`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('environment')).toBe(env);
      req.flush(mockResponse);
    });

    it('should list deployments filtered by both status and environment', () => {
      const status = 'SUCCEEDED';
      const env = 'staging';
      const mockResponse = {
        items: [],
        next_cursor: null
      };

      service.listDeployments(status, env).subscribe();

      const req = httpMock.expectOne(`${apiUrl}/deployments?status=${status}&environment=${env}`);
      expect(req.request.params.get('status')).toBe(status);
      expect(req.request.params.get('environment')).toBe(env);
      req.flush(mockResponse);
    });
  });

  describe('getDeployment', () => {
    it('should get a specific deployment by ID', () => {
      const deploymentId = 'dep-123';
      const mockDeployment: Deployment = {
        id: deploymentId,
        model_version_id: 'ver-456',
        environment: 'production',
        status: DeploymentStatus.SUCCEEDED,
        idempotency_key: 'key-abc',
        requested_at: '2024-01-01',
        completed_at: '2024-01-01',
        rolled_back_from_id: null,
        attempt_count: 1,
        failure_reason: null,
        model_name: 'fraud-detector',
        version_number: '2.0.0'
      };

      service.getDeployment(deploymentId).subscribe(deployment => {
        expect(deployment).toEqual(mockDeployment);
        expect(deployment.id).toBe(deploymentId);
      });

      const req = httpMock.expectOne(`${apiUrl}/deployments/${deploymentId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockDeployment);
    });

    it('should handle deployment not found (404)', () => {
      const deploymentId = 'dep-nonexistent';

      service.getDeployment(deploymentId).subscribe(
        () => fail('should have failed with 404 error'),
        error => {
          expect(error.status).toBe(404);
        }
      );

      const req = httpMock.expectOne(`${apiUrl}/deployments/${deploymentId}`);
      req.flush({ detail: 'Deployment not found' }, { status: 404, statusText: 'Not Found' });
    });
  });

  describe('retryDeployment', () => {
    it('should retry a failed deployment via POST request', () => {
      const deploymentId = 'dep-789';
      const mockResponse: Deployment = {
        id: deploymentId,
        model_version_id: 'ver-123',
        environment: 'staging',
        status: DeploymentStatus.REQUESTED,
        idempotency_key: 'key-retry',
        requested_at: '2024-01-01',
        completed_at: null,
        rolled_back_from_id: null,
        attempt_count: 2,
        failure_reason: null,
        model_name: 'test-model',
        version_number: '1.0.0'
      };

      service.retryDeployment(deploymentId).subscribe(deployment => {
        expect(deployment.id).toBe(deploymentId);
        expect(deployment.attempt_count).toBe(2);
        expect(deployment.status).toBe(DeploymentStatus.REQUESTED);
      });

      const req = httpMock.expectOne(`${apiUrl}/deployments/${deploymentId}/retry`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({});
      req.flush(mockResponse);
    });

    it('should handle max retry attempts exceeded (400)', () => {
      const deploymentId = 'dep-max-retries';

      service.retryDeployment(deploymentId).subscribe(
        () => fail('should have failed with 400 error'),
        error => {
          expect(error.status).toBe(400);
        }
      );

      const req = httpMock.expectOne(`${apiUrl}/deployments/${deploymentId}/retry`);
      req.flush({ detail: 'Max retry attempts reached' }, { status: 400, statusText: 'Bad Request' });
    });
  });

  describe('rollbackDeployment', () => {
    it('should rollback a deployment via POST request', () => {
      const deploymentId = 'dep-current';
      const mockResponse: Deployment = {
        id: 'dep-rollback-new',
        model_version_id: 'ver-previous',
        environment: 'production',
        status: DeploymentStatus.REQUESTED,
        idempotency_key: `rollback-${deploymentId}`,
        requested_at: new Date().toISOString(),
        completed_at: null,
        rolled_back_from_id: deploymentId,
        attempt_count: 0,
        failure_reason: null,
        model_name: 'test-model',
        version_number: '1.0.0'
      };

      service.rollbackDeployment(deploymentId).subscribe(deployment => {
        expect(deployment.rolled_back_from_id).toBe(deploymentId);
        expect(deployment.status).toBe(DeploymentStatus.REQUESTED);
      });

      const req = httpMock.expectOne(`${apiUrl}/deployments/${deploymentId}/rollback`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({});
      req.flush(mockResponse);
    });

    it('should handle no prior deployment for rollback (400)', () => {
      const deploymentId = 'dep-first';

      service.rollbackDeployment(deploymentId).subscribe(
        () => fail('should have failed with 400 error'),
        error => {
          expect(error.status).toBe(400);
        }
      );

      const req = httpMock.expectOne(`${apiUrl}/deployments/${deploymentId}/rollback`);
      req.flush({ detail: 'No prior successful deployment to rollback to' }, { status: 400, statusText: 'Bad Request' });
    });
  });
});

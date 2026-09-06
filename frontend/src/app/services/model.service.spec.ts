import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ModelService } from './model.service';
import {
  Model,
  ModelCreate,
  ModelVersion,
  ModelVersionCreate,
  LifecyclePromoteRequest,
  LifecycleStage
} from '../models';
import { environment } from '../../environments/environment';

describe('ModelService', () => {
  let service: ModelService;
  let httpMock: HttpTestingController;
  const apiUrl = `${environment.apiUrl}/api/v1`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ModelService]
    });
    service = TestBed.inject(ModelService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('createModel', () => {
    it('should create a model via POST request', () => {
      const mockModelCreate: ModelCreate = {
        name: 'test-model',
        owner: 'test-owner',
        description: 'Test description'
      };

      const mockResponse: Model = {
        id: 'model-123',
        ...mockModelCreate,
        created_at: new Date().toISOString()
      };

      service.createModel(mockModelCreate).subscribe(model => {
        expect(model).toEqual(mockResponse);
        expect(model.id).toBe('model-123');
        expect(model.name).toBe('test-model');
      });

      const req = httpMock.expectOne(`${apiUrl}/models`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(mockModelCreate);
      req.flush(mockResponse);
    });
  });

  describe('listModels', () => {
    it('should list models without cursor', () => {
      const mockResponse = {
        items: [
          { id: 'model-1', name: 'model-1', owner: 'owner-1', description: '', created_at: '2024-01-01' }
        ],
        next_cursor: null
      };

      service.listModels().subscribe(response => {
        expect(response.items.length).toBe(1);
        expect(response.items[0].name).toBe('model-1');
        expect(response.next_cursor).toBeNull();
      });

      const req = httpMock.expectOne(`${apiUrl}/models`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.keys().length).toBe(0);
      req.flush(mockResponse);
    });

    it('should list models with cursor parameter', () => {
      const cursor = 'cursor-abc';
      const mockResponse = {
        items: [],
        next_cursor: 'cursor-def'
      };

      service.listModels(cursor).subscribe(response => {
        expect(response.next_cursor).toBe('cursor-def');
      });

      const req = httpMock.expectOne(`${apiUrl}/models?cursor=${cursor}`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('cursor')).toBe(cursor);
      req.flush(mockResponse);
    });
  });

  describe('getModel', () => {
    it('should get a specific model by ID', () => {
      const modelId = 'model-123';
      const mockModel: Model = {
        id: modelId,
        name: 'test-model',
        owner: 'test-owner',
        description: 'Test description',
        created_at: new Date().toISOString()
      };

      service.getModel(modelId).subscribe(model => {
        expect(model).toEqual(mockModel);
        expect(model.id).toBe(modelId);
      });

      const req = httpMock.expectOne(`${apiUrl}/models/${modelId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockModel);
    });
  });

  describe('createVersion', () => {
    it('should create a model version via POST request', () => {
      const modelId = 'model-123';
      const versionCreate: ModelVersionCreate = {
        version_number: '1.0.0',
        framework: 'TensorFlow',
        algorithm: 'CNN',
        artifact_uri: 's3://bucket/model.pkl',
        tags: { env: 'dev' }
      };

      const mockVersion: ModelVersion = {
        id: 'ver-456',
        model_id: modelId,
        ...versionCreate,
        lifecycle_stage: LifecycleStage.DRAFT,
        row_version: 1,
        created_at: new Date().toISOString()
      };

      service.createVersion(modelId, versionCreate).subscribe(version => {
        expect(version).toEqual(mockVersion);
        expect(version.id).toBe('ver-456');
        expect(version.lifecycle_stage).toBe(LifecycleStage.DRAFT);
      });

      const req = httpMock.expectOne(`${apiUrl}/models/${modelId}/versions`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(versionCreate);
      req.flush(mockVersion);
    });
  });

  describe('listVersions', () => {
    it('should list versions for a specific model', () => {
      const modelId = 'model-123';
      const mockResponse = {
        items: [
          {
            id: 'ver-1',
            model_id: modelId,
            version_number: '1.0.0',
            framework: 'TensorFlow',
            algorithm: 'CNN',
            artifact_uri: 's3://bucket/v1.pkl',
            lifecycle_stage: LifecycleStage.PRODUCTION,
            row_version: 5,
            tags: {},
            created_at: '2024-01-01'
          }
        ],
        next_cursor: null
      };

      service.listVersions(modelId).subscribe(response => {
        expect(response.items.length).toBe(1);
        expect(response.items[0].lifecycle_stage).toBe(LifecycleStage.PRODUCTION);
      });

      const req = httpMock.expectOne(`${apiUrl}/models/${modelId}/versions`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('promoteLifecycle', () => {
    it('should promote lifecycle stage via PATCH request', () => {
      const modelId = 'model-123';
      const versionId = 'ver-456';
      const promoteRequest: LifecyclePromoteRequest = {
        target_stage: LifecycleStage.VALIDATED,
        row_version: 1
      };

      const mockUpdatedVersion: ModelVersion = {
        id: versionId,
        model_id: modelId,
        version_number: '1.0.0',
        framework: 'TensorFlow',
        algorithm: 'CNN',
        artifact_uri: 's3://bucket/model.pkl',
        lifecycle_stage: LifecycleStage.VALIDATED,
        row_version: 2,
        tags: {},
        created_at: '2024-01-01'
      };

      service.promoteLifecycle(modelId, versionId, promoteRequest).subscribe(version => {
        expect(version.lifecycle_stage).toBe(LifecycleStage.VALIDATED);
        expect(version.row_version).toBe(2);
      });

      const req = httpMock.expectOne(`${apiUrl}/models/${modelId}/versions/${versionId}/lifecycle`);
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual(promoteRequest);
      req.flush(mockUpdatedVersion);
    });

    it('should handle optimistic locking conflict (409)', () => {
      const modelId = 'model-123';
      const versionId = 'ver-456';
      const promoteRequest: LifecyclePromoteRequest = {
        target_stage: LifecycleStage.APPROVED,
        row_version: 1
      };

      service.promoteLifecycle(modelId, versionId, promoteRequest).subscribe(
        () => fail('should have failed with 409 error'),
        error => {
          expect(error.status).toBe(409);
        }
      );

      const req = httpMock.expectOne(`${apiUrl}/models/${modelId}/versions/${versionId}/lifecycle`);
      req.flush({ detail: 'Stale version' }, { status: 409, statusText: 'Conflict' });
    });
  });
});

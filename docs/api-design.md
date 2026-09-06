# API Design

## Principles
- RESTful resource-oriented endpoints under `/api/v1`
- Typed request/response with Pydantic models
- Consistent error schema across all endpoints
- Idempotency where required (deployment requests)
- Pagination for all list endpoints (cursor-based, not offset/limit)

## Core Endpoints

### Models
- `POST /api/v1/models` — create model
- `GET /api/v1/models` — list models (paginated)
- `GET /api/v1/models/{model_id}` — get model details
- `POST /api/v1/models/{model_id}/versions` — create version
- `GET /api/v1/models/{model_id}/versions` — list versions
- `PATCH /api/v1/models/{model_id}/versions/{version_id}/lifecycle` — promote lifecycle stage (requires `row_version` for optimistic locking)

### Deployments
- `POST /api/v1/deployments` — request deployment (returns `202`, requires `idempotency_key`)
- `GET /api/v1/deployments` — list deployments (paginated, filterable by status/environment)
- `GET /api/v1/deployments/{deployment_id}` — get deployment status
- `POST /api/v1/deployments/{deployment_id}/retry` — retry failed deployment
- `POST /api/v1/deployments/{deployment_id}/rollback` — rollback to prior version

### Monitoring
- `GET /api/v1/models/{model_id}/versions/{version_id}/metrics` — get metric snapshots (time-range required)
- `POST /api/v1/metrics` — ingest metric snapshot (internal endpoint, called by deployment targets)

### Health
- `GET /api/v1/health` — system health (DB connectivity, worker heartbeat)

## Error Schema
All errors follow this shape:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "lifecycle_stage cannot skip from DRAFT to PRODUCTION",
    "correlation_id": "abc-123",
    "details": { "current_stage": "DRAFT", "requested_stage": "PRODUCTION" }
  }
}
```

**Error codes**: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `UNAUTHORIZED`, `INTERNAL_ERROR`.

## Idempotency
`POST /deployments` requires an `idempotency_key` in the request body. Duplicate keys return the existing `Deployment` (status may have changed since first request) instead of creating a new row. Key is a UUID generated client-side, scoped per deployment intent — retrying the same logical deployment uses the same key; deploying a different version uses a different key.

## Pagination
List endpoints return:
```json
{
  "items": [...],
  "next_cursor": "opaque-string-or-null"
}
```
Pass `?cursor=opaque-string` to fetch the next page. No page numbers — cursors are opaque and tied to `(status, created_at)` index order.

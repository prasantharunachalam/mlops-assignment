# Architecture

## Context
An industrial organization runs ML models across multiple plants and environments. Models need a registration point, an approval gate before production use, a way to deploy and roll back safely, and visibility into how each deployed version is performing.

## Scope
**In scope**: model/version registry, approval and lifecycle promotion, deployment with retry/rollback, metric monitoring, Angular operational views.
**Out of scope**: actual model training, real Kubernetes provisioning (simulated), authentication implementation (design only — see Security), multi-tenancy (see roadmap.md).

## Architecture Overview

```
Angular UI  →  FastAPI (REST, /api/v1)  →  PostgreSQL
                     │
                     └──→  Background Worker (deployment processor)
                                  │
                                  └──→  Simulated Deployment Target
```

Angular never talks to Postgres or the worker directly — every interaction goes through the versioned REST API. This is the isolation boundary referenced throughout this document.

## Components

| Component | Responsibility |
|---|---|
| Registry Service | Model/version CRUD, approval-status transitions |
| Deployment Service | Accepts deployment requests, enforces lifecycle gates, writes `Deployment` rows |
| Deployment Worker | Polls `REQUESTED` deployments, drives them through `VALIDATING → DEPLOYING → SUCCEEDED/FAILED` |
| Monitoring Service | Ingests and serves metric snapshots per model version |
| Angular App | Registry views, deployment tracking, monitoring dashboard, event timeline |

## Domain Model

**Model** — `id, name, description, owner, created_at`

**ModelVersion** — `id, model_id (FK), version_number, framework, algorithm, artifact_uri, training_data_ref, tags (JSONB), lifecycle_stage, row_version (int, for optimistic locking), created_at, updated_at`
`lifecycle_stage`: `DRAFT → VALIDATED → APPROVED → STAGING → PRODUCTION → ARCHIVED`

**Deployment** — `id, model_version_id (FK), environment, status, idempotency_key (unique), requested_at, completed_at, rolled_back_from_id (nullable FK to prior Deployment)`
`status`: `REQUESTED → VALIDATING → DEPLOYING → SUCCEEDED | FAILED | ROLLED_BACK`

**MetricSnapshot** — `id, model_version_id (FK), captured_at, latency_ms, throughput_rps, error_rate, quality_score, drift_score, availability`

## Key Workflows

**Register → Approve → Deploy**
1. `POST /models` → `POST /models/{id}/versions` — version starts at `DRAFT`.
2. Validation and approval move `lifecycle_stage` forward one step at a time; no skipping stages.
3. `POST /deployments` is rejected with `409` unless `lifecycle_stage` is `APPROVED` or later, and `STAGING` is required before `PRODUCTION` is permitted.
4. Worker processes the request asynchronously (see ADR-001).

**Rollback**
Rollback creates a **new** `Deployment` row referencing the prior successful deployment (`rolled_back_from_id`), rather than mutating the failed one. This preserves a complete audit trail — the deployment history is append-only.

## Reliability
- **Idempotency**: `idempotency_key` is unique per deployment request. A duplicate key returns the existing `Deployment` instead of creating a second one.
- **Retry**: `POST /deployments/{id}/retry` is only valid from `FAILED`; it resets status to `REQUESTED` and increments an `attempt_count`, capped at 3.
- **Rollback safety**: only permitted if a prior `SUCCEEDED` deployment exists for the same `model_id` + `environment` pair. No prior success, no rollback target — the API returns `409`.

## Security
Not implemented in this build (out of scope per Scope section), but designed for: JWT-based auth, with a `role` claim (`viewer`, `approver`, `deployer`). Approval and production-deployment endpoints check role server-side; Angular hides but does not rely on hiding UI elements for enforcement.

## Observability
- Structured JSON logs, one line per request, including a `correlation_id` generated at the API edge and passed through to worker logs for the same deployment.
- `GET /health` checks DB connectivity and worker heartbeat (last poll timestamp within 10s).
- Failures are classified at write time (`VALIDATION_ERROR`, `TARGET_UNREACHABLE`, `TIMEOUT`) and stored on the `Deployment` row — not inferred later from logs.
- Proposed dashboard: deployment success rate (rolling 24h), p95 deployment duration, active drift alerts, worker queue depth.

## Scaling
**100 → 10,000 models**: list endpoints (`GET /models`, `GET /deployments`) use cursor-based pagination and are indexed on `(status, created_at)`. Model list reads are cached with a 30s TTL — writes are infrequent relative to reads in this domain. Metric ingestion is the highest-volume path; see partitioning note below.

**Metric volume**: `MetricSnapshot` is partitioned by `captured_at` (weekly range partitions). Queries for "current" dashboards hit only the latest partition; historical queries are explicitly time-bounded. Partitions older than 90 days roll to a cheaper storage tier.

## Trade-offs
- Chose an in-process worker over Celery/Redis for scope-appropriate simplicity — see ADR-003 for the production migration path.
- Chose optimistic locking (`row_version` column) over pessimistic row locks for promotion conflicts — avoids lock contention on read-heavy registry traffic, at the cost of requiring client-side retry on `409`.
- Chose append-only deployment history over mutable status updates — larger table growth, but audit trail correctness matters more in a regulated industrial setting.

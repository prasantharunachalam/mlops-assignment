# Leadership Questions

**1. How would this scale from 100 to 10,000 models?**
Index `(status, created_at)` on `Model` and `ModelVersion`, cursor-based pagination on all list endpoints, 30s-TTL cache on model list reads. At 10,000 models the bottleneck shifts from the registry to metric ingestion volume — see Q6.

**2. How are conflicting promotions prevented?**
Optimistic locking. `ModelVersion.row_version` increments on every state change. A promotion request includes the `row_version` it read; if it doesn't match the current value, the API returns `409` and the client re-fetches and retries. No database-level locks held across the request.

**3. How is external success / internal database failure reconciled?**
The worker writes `DEPLOYING` before calling the external target, and the external call is idempotent (same deployment ID passed each attempt). A scheduled reconciliation sweep (every 60s) checks any `Deployment` stuck in `DEPLOYING` for more than 5 minutes against the external target's actual status and corrects the row — covers the case where the external call succeeded but the DB write to `SUCCEEDED` failed.

**4. How are multiple model runtimes supported?**
A `DeploymentTarget` interface with one implementation per runtime (Kubernetes, edge device, batch scoring service). `Deployment` stores `runtime_type`; the worker dispatches to the matching adapter. Adding a runtime means adding an adapter, not changing the domain model.

**5. How would multi-tenancy work?**
Add `tenant_id` to `Model`, enforced at the query layer via a required filter in every repository method (not optional). Postgres row-level security as a defense-in-depth layer once the application-layer filter is proven. No cross-tenant joins permitted by design.

**6. How are large metric volumes partitioned?**
`MetricSnapshot` uses weekly range partitions on `captured_at`. Dashboard queries hit only the current partition; historical queries require an explicit date range. Partitions older than 90 days move to cheaper storage and are excluded from the default query path.

**7. How is unsafe rollback prevented?**
Rollback requires a prior `SUCCEEDED` deployment for the same `model_id` + `environment`. No prior success exists → `409`. Rollback creates a new `Deployment` row rather than mutating history, so a bad rollback is itself reversible.

**8. How are zero-downtime schema migrations handled?**
Expand-contract pattern via Alembic: add new columns nullable, deploy code that writes both old and new, backfill, then drop the old column in a later release. Index creation uses `CREATE INDEX CONCURRENTLY` to avoid locking large tables.

**9. How is Angular isolated from backend internals?**
Angular talks only to the versioned `/api/v1` REST contract via typed DTOs generated from the OpenAPI spec — never to internal domain objects directly. Backend refactors that don't change the API contract require zero frontend changes.

**10. How would work be split across teams?**
See delivery-plan.md — split by bounded context (Registry, Deployment/Worker, Monitoring, Frontend), each owning its endpoints end-to-end rather than splitting by layer (frontend team / backend team), which minimizes cross-team blocking.

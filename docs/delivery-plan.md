# Delivery Plan — 4-Engineer Team, 2-Week Sprint

| Engineer | Workstream | Depends On |
|---|---|---|
| A | Registry service (Model/ModelVersion CRUD, lifecycle state machine, optimistic locking) | Domain model sign-off (day 1) |
| B | Deployment service + worker (async processing, retry, rollback, idempotency) | A's `ModelVersion` schema |
| C | Monitoring service (metric ingestion endpoint, partitioning) + observability (logging, correlation IDs, health) | Can start day 1, independent of A/B |
| D | Angular frontend (registry views, deployment tracking, dashboard, event timeline) | OpenAPI spec frozen (day 2), then works against mocked responses until A/B/C endpoints land |

**Sequencing note**: the OpenAPI spec is frozen after domain-model sign-off on day 1, before any endpoint is implemented — this unblocks D immediately instead of leaving frontend work waiting on backend completion. Backend engineers implement against the same frozen contract; D's mocks are simply superseded by real responses as each endpoint ships, with no rework.

**Integration checkpoints**: end of day 3 (registry + frontend registry view working end-to-end), end of day 7 (deployment flow working end-to-end), end of day 10 (monitoring dashboard live), final 3 days for hardening and the acceptance-scenario pass.

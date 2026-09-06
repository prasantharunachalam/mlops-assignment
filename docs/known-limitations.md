# Known Limitations

## Scope Boundaries (Intentional)
- **No authentication/authorization**: design documented in architecture.md Security section, not implemented. All endpoints are open in this build.
- **Simulated deployment target**: worker logs success/failure without actually provisioning infrastructure. Real Kubernetes adapter requires only swapping the `DeploymentTarget` implementation, no domain-model change.
- **No multi-tenancy**: single-tenant data model. Adding `tenant_id` is a schema change + query-layer filter (see leadership-qna.md Q5).
- **In-process worker**: does not survive restarts. Production path is Celery/Redis (see ADR-003).

## Technical Constraints
- **Metric partitioning**: implemented from day one but requires manual partition creation for future weeks (automated via a cron job in production, out of scope here).
- **No real-time dashboard updates**: Angular polls every 5s. Production would use Server-Sent Events or WebSocket for live metric push.
- **Reconciliation sweep**: manual trigger only in this build (production would run as a scheduled background task).

## Accepted Trade-offs
- **Append-only deployment history**: larger table growth, but audit correctness and rollback safety matter more in a regulated industrial setting.
- **Optimistic locking over pessimistic**: avoids lock contention on registry reads, at the cost of requiring client-side retry on `409` conflicts.
- **Postgres JSONB for tags**: schema flexibility without wide sparse columns, but no database-level validation (validated in API layer only).

## Future Enhancements (Roadmap)
See [roadmap.md](roadmap.md) for prioritized next steps.

# Roadmap

## Near-Term (this submission)
- Model/version registry with lifecycle gating
- Async deployment with retry and audit-preserving rollback
- Metric ingestion and monitoring dashboard
- Angular views for registry, deployment, monitoring, event timeline
- Structured logging with correlation IDs, health endpoint

## Future
- **Authentication & authorization**: JWT + role claims, enforced server-side on approval/deploy endpoints (design exists, not implemented — see architecture.md Security)
- **Multi-tenancy**: `tenant_id` scoping across all tables and queries (see leadership-qna.md Q5)
- **Production worker**: migrate from in-process poller to Celery/Redis for restart durability (see ADR-003)
- **Real deployment targets**: replace the simulated target with a Kubernetes adapter behind the existing `DeploymentTarget` interface
- **Drift-triggered alerts**: automated notification when `drift_score` crosses a threshold, rather than dashboard-only visibility

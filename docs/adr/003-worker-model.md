# ADR-003: In-Process Background Worker (Not an External Queue)

## Status
Accepted — scoped for assignment size, with a stated production path.

## Context
ADR-001 requires a worker to process deployments asynchronously. Options range from an in-process task runner to a dedicated broker (Redis/RabbitMQ) with Celery or RQ.

## Decision
Use FastAPI's in-process background task runner backed by a `deployments` table polled every 2 seconds (`SELECT ... WHERE status = 'REQUESTED' FOR UPDATE SKIP LOCKED`). No external broker for this build.

## Alternatives Considered
- **Celery + Redis**: production-grade durability — jobs survive a process restart. Rejected for this scope: adds a broker dependency and operational surface disproportionate to the assignment's size and timebox.
- **Cloud-managed queue (SQS/Pub-Sub)**: same durability benefit, adds a cloud dependency the local Docker Compose setup can't replicate. Rejected for the same reason.

## Consequences
### Positive
- Zero extra infrastructure — `docker compose up` is the entire footprint.
- `FOR UPDATE SKIP LOCKED` gives safe multi-worker polling without a broker.

### Negative
- A worker crash mid-deployment leaves the row in `DEPLOYING` with no automatic recovery; requires a manual or scheduled reconciliation sweep (see risk-register.md).
- Does not survive horizontal scaling gracefully — polling multiple replicas against the same table works but wastes cycles past 3–4 workers.

## Follow-up Actions
- Production migration path: swap the poller for a Celery worker consuming the same `deployments` table via an outbox row: no domain-model change required, only the dispatch mechanism.

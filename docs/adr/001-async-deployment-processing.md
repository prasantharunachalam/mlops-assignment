# ADR-001: Deployment Processing Is Asynchronous

## Status
Accepted

## Context
A deployment request involves validating the target version, provisioning a runtime, and confirming health — work that takes seconds to minutes and can fail independently at each step. The API must respond quickly regardless of how long the underlying deployment takes.

## Decision
`POST /deployments` validates the request, writes a `Deployment` row in `REQUESTED` state, and returns `202 Accepted` immediately. A background worker picks up the row, transitions it through `VALIDATING → DEPLOYING → SUCCEEDED/FAILED`, and writes status updates the client polls via `GET /deployments/{id}`.

## Alternatives Considered
- **Synchronous request/response**: simpler, but ties up an API worker thread for the full deployment duration and forces the client to hold a connection open for minutes. Rejected — doesn't scale past a handful of concurrent deployments.
- **Client-side polling of an external orchestrator directly**: removes our worker but couples the Angular client to deployment-target specifics. Rejected — breaks the API isolation goal (see architecture.md, Reliability).

## Consequences
### Positive
- API stays responsive under deployment load.
- Retry and rollback become state transitions on an existing row, not new request types.

### Negative
- Requires a worker process and a job queue, adding one more moving part to operate.
- Client must poll or use a webhook for completion status; no synchronous confirmation.

## Follow-up Actions
- Define worker durability model in ADR-003.

# Test Strategy

## Approach
Testing is layered — unit tests for domain logic isolation, integration tests for database and worker interaction, Angular component tests for UI state transitions, and acceptance-scenario tests for end-to-end workflows. No mocking of the database in integration tests; use a real PostgreSQL container to catch schema/constraint bugs early.

## Unit Tests
**Backend**: service-layer methods tested in isolation with repository dependencies mocked. Focus: state-machine transitions (lifecycle promotion rules), idempotency-key collision handling, retry-cap enforcement, rollback-target validation.

**Frontend**: Angular component logic tested with mocked HTTP responses. Focus: deployment-status polling, error-state rendering, form validation before API submission.

## Integration Tests
**Backend**: FastAPI `TestClient` against a test-scoped PostgreSQL database. Tests span the full request → repository → database → response cycle. Focus: foreign-key enforcement, optimistic-locking conflict detection (`409` on stale `row_version`), worker state transitions (mock the external deployment target, real database writes).

**Coverage target**: every endpoint's success path + at least one failure path (validation error, conflict, not-found).

## Acceptance Scenarios
End-to-end tests that validate the 10 acceptance criteria from the assignment brief. Run against `docker compose` with backend, frontend, and database all live. Uses Playwright to drive the Angular UI and verifies the resulting database state.

Examples:
- Register model → create two versions → approve one → reject deployment of unapproved version to Production (expect `409`).
- Deploy approved version → simulate failure → retry → verify `attempt_count` increments and deployment succeeds.
- Deploy to Production → rollback → verify new `Deployment` row with `rolled_back_from_id` set, original row unchanged.

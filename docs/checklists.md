# Checklists

## Code Review
- [ ] State transitions validated against the allowed-transition list, not assumed
- [ ] Every write path is idempotent or explicitly documented as not
- [ ] New endpoints have unit tests for the success path and at least one failure path
- [ ] No raw SQL string concatenation — parameterized queries only
- [ ] Error responses follow the shared error schema, not ad-hoc shapes
- [ ] Logs include `correlation_id`; no `print()` statements
- [ ] No secrets, connection strings, or credentials in the diff
- [ ] Database migrations are additive (expand-contract), not destructive, unless explicitly reviewed
- [ ] API changes are reflected in the OpenAPI spec in the same PR

## Production Readiness
- [ ] `GET /health` reports DB and worker status, not just process liveness
- [ ] Rollback path tested against a real prior deployment, not just the happy path
- [ ] Retry cap in place (no unbounded retry loops)
- [ ] Metric table partitioning strategy active before volume, not retrofitted after
- [ ] Secrets loaded from environment, not committed — `.env.example` present, `.env` gitignored
- [ ] CI runs lint, unit tests, and integration tests before merge
- [ ] Known limitations documented in README, not left implicit

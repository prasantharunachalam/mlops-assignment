# Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Worker crash mid-deployment leaves row stuck in `DEPLOYING` | Medium | Medium | Reconciliation sweep (60s interval) resolves stuck rows against external target status |
| Concurrent promotion requests corrupt lifecycle state | Medium | High | Optimistic locking via `row_version`; conflicting writes rejected with `409` |
| Unbounded `MetricSnapshot` growth degrades query performance | High (over time) | Medium | Weekly partitioning + 90-day hot/cold split from day one, not retrofitted later |
| No authentication in this build allows any client to approve/deploy | High (in this build) | High | Explicitly out of scope; design documented in architecture.md Security section; must be closed before any real deployment |
| Retry loop on a permanently failing target exhausts worker capacity | Low | Medium | Retry capped at 3 attempts (`attempt_count`), then requires manual intervention |
| Duplicate deployment requests from a flaky client create duplicate work | Medium | Low | `idempotency_key` uniqueness constraint returns existing deployment instead of creating a new one |

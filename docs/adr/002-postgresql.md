# ADR-002: PostgreSQL as System of Record

## Status
Accepted

## Context
The domain has strict referential relationships — a `Deployment` must reference a valid `ModelVersion`, which must reference a valid `Model` — plus semi-structured fields (tags, metadata) that vary by framework.

## Decision
PostgreSQL is the primary datastore. Structured relationships (Model → ModelVersion → Deployment) use foreign keys with `ON DELETE RESTRICT`. Variable metadata (tags, framework-specific config) uses `JSONB` columns, queryable via GIN indexes where needed.

## Alternatives Considered
- **SQLite**: sufficient for local development but lacks concurrent-write safety needed once the worker and API write to the same rows. Rejected for anything beyond a dev fallback.
- **Document store (MongoDB)**: fits the variable-metadata need but weakens the referential integrity guarantees this domain depends on — approval gates and rollback safety both rely on foreign-key-enforced consistency. Rejected.

## Consequences
### Positive
- Foreign keys enforce that a deployment can never reference a non-existent version — no application-level integrity checks needed for this invariant.
- `JSONB` gives schema flexibility for framework-specific metadata without a wide, sparse column set.

### Negative
- Schema migrations require more care than a schemaless store (see architecture.md, Scaling — zero-downtime migration approach).
- JSONB fields are not validated at the database layer; validation lives entirely in the API.

## Follow-up Actions
- None. SQLite remains available as a local test fixture via a `DATABASE_URL` override.

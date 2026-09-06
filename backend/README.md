# MLOps Platform - Backend

FastAPI backend for MLOps model registry and deployment management.

## Structure

```
app/
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic request/response schemas
├── repositories/   # Data access layer
├── services/       # Business logic
├── api/v1/         # API route handlers
├── worker/         # Background deployment worker
└── utils/          # Utilities (logging, errors)
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Docker

```bash
docker compose up backend
```

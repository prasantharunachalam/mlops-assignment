#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting deployment worker in background..."
python -m app.worker.main &

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

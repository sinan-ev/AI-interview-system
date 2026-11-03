#!/bin/bash
set -e

echo "[1/2] Applying database migrations..."
alembic upgrade head

echo "[2/2] Starting FastAPI Uvicorn Server on http://0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

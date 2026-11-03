@echo off
REM Start Local Development Server for Windows
echo [1/2] Applying database migrations...
alembic upgrade head

echo [2/2] Starting FastAPI Uvicorn Server on http://localhost:8000...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

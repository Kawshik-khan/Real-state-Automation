#!/bin/sh
set -e

echo "====================================================="
echo "  GLG Assets Social AI OS — Container Entrypoint"
echo "====================================================="

# Step 1: Run Alembic Database Migrations
echo "[entrypoint] Running Alembic database migrations..."
if [ -f "alembic.ini" ] || [ -f "../alembic.ini" ]; then
    alembic upgrade head || echo "[entrypoint] Alembic migration warning: continuing container startup"
else
    echo "[entrypoint] No alembic.ini found, skipping migrations."
fi

# Step 2: Launch Uvicorn FastAPI Production App
echo "[entrypoint] Launching FastAPI backend server on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

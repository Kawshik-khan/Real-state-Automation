#!/bin/sh
set -e

# Guarantee PYTHONPATH includes /app so all CLI tools (alembic, uvicorn, python) can import app
export PYTHONPATH="/app:${PYTHONPATH:-}"

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

# Step 2: Determine worker count (default 2, configurable via WEB_CONCURRENCY)
WORKERS="${WEB_CONCURRENCY:-2}"
echo "[entrypoint] Workers: ${WORKERS}"

# Step 3: Launch Uvicorn FastAPI Production App
echo "[entrypoint] Launching FastAPI backend server on 0.0.0.0:8000..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WORKERS}" \
    --log-level info \
    --access-log \
    --proxy-headers \
    --forwarded-allow-ips "*"

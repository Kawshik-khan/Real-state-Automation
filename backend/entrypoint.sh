#!/bin/sh
set -e

# Guarantee PYTHONPATH includes /app so all CLI tools (alembic, uvicorn, python) can import app
export PYTHONPATH="/app:${PYTHONPATH:-}"

# Suppress known upstream LangChain/LangGraph deprecation warnings before Python interpreter initializes
export PYTHONWARNINGS="ignore"

echo "====================================================="
echo "  GLG Assets Social AI OS — Container Entrypoint"
echo "====================================================="

# Step 1: Run Alembic Database Migrations
echo "[entrypoint] Checking database migration configuration..."
if [ -z "${DATABASE_URL}" ] || echo "${DATABASE_URL}" | grep -qE "localhost|127\.0\.0\.1"; then
    if [ -z "${DATABASE_URL}" ]; then
        echo "[entrypoint] Notice: DATABASE_URL is not set. Skipping Alembic database migrations."
    else
        echo "[entrypoint] Notice: DATABASE_URL points to localhost in a container. Skipping Alembic database migrations."
    fi
    echo "[entrypoint] (Set DATABASE_URL to your Supabase or managed PostgreSQL URL to enable automatic migrations)"
elif [ -f "alembic.ini" ] || [ -f "../alembic.ini" ]; then
    echo "[entrypoint] Running Alembic database migrations against configured database..."
    alembic upgrade head || echo "[entrypoint] Alembic migration warning: continuing container startup"
else
    echo "[entrypoint] No alembic.ini found, skipping migrations."
fi

# Step 2: Determine worker count (default 2, configurable via WEB_CONCURRENCY)
WORKERS="${WEB_CONCURRENCY:-2}"
echo "[entrypoint] Workers: ${WORKERS}"

# Step 3: Launch Uvicorn FastAPI Production App
echo "[entrypoint] Launching FastAPI backend server on 0.0.0.0:${PORT:-8000}..."
exec python -W ignore -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WORKERS}" \
    --log-level info \
    --access-log \
    --proxy-headers \
    --forwarded-allow-ips "*"

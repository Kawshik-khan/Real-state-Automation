"""Shared test fixtures and CI-safe environment setup.

This conftest runs BEFORE any app imports, setting CI-safe env defaults
so tests pass in GitHub Actions (no database, no API keys, no Gmail).
"""

import os
import pytest

# ── CI-safe environment defaults ──
# These are only set if NOT already defined (won't override .env on local dev)
_CI_DEFAULTS = {
    "APP_NAME": "GLG Assets Test",
    "DEBUG": "false",
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/glg_assets_test",
    "AUTOMATION_SHARED_SECRET": "test-ci-secret-key",
    "JWT_SECRET": "test-jwt-secret-key-for-ci-minimum-32-chars-long",
    "PASSWORD_HASH_SALT": "glg_assets_salt_2026",
    "DEFAULT_TENANT_ID": "glg-assets-test",
    "CORS_ORIGINS": "*",
    "OPENAI_API_KEY": "",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_BASE_URL": "",
    "VECTOR_STORE_PROVIDER": "pgvector",
    "PINECONE_API_KEY": "",
    "SUPABASE_URL": "",
    "SUPABASE_SERVICE_ROLE_KEY": "",
    "GMAIL_USER_EMAIL": "",
    "GMAIL_APP_PASSWORD": "",
}

for key, value in _CI_DEFAULTS.items():
    os.environ.setdefault(key, value)


# ── Now safe to import app modules ──
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.core.security import create_access_token
from app.models.user import UserRole


@pytest.fixture(scope="session")
def test_client():
    """Reusable FastAPI TestClient for the entire test session."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers():
    """Headers with the CI automation secret."""
    return {"X-Automation-Secret": settings.automation_shared_secret}


@pytest.fixture(scope="session")
def dev_token():
    """JWT token for a developer user."""
    return create_access_token({
        "sub": "developer@glgassets.com",
        "email": "developer@glgassets.com",
        "role": UserRole.DEVELOPER.value,
        "tenant_id": settings.default_tenant_id,
    })


@pytest.fixture(scope="session")
def dev_headers(dev_token):
    """Authorization headers for developer role."""
    return {"Authorization": f"Bearer {dev_token}"}


@pytest.fixture(scope="session")
def admin_token():
    """JWT token for an admin user."""
    return create_access_token({
        "sub": "admin@glgassets.com",
        "email": "admin@glgassets.com",
        "role": UserRole.ADMIN.value,
        "tenant_id": settings.default_tenant_id,
    })


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """Authorization headers for admin role."""
    return {"Authorization": f"Bearer {admin_token}"}

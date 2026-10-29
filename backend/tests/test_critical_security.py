"""Regression tests for the Critical findings in the 2026-10-29 production-readiness audit."""

import asyncio

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.security import create_access_token
from app.main import app
from app.models.user import UserRole
from app.services.ai_control_plane.control_plane_service import control_plane_service
from app.services.user_service import user_service

client = TestClient(app)


def _bearer(role: UserRole) -> dict:
    token = create_access_token({"sub": f"usr-{role.value}", "email": f"{role.value}@glgassets.com", "role": role.value})
    return {"Authorization": f"Bearer {token}"}


# ── C4: public default secrets are detected ──

def test_default_secrets_are_flagged(monkeypatch):
    for name in ("AUTOMATION_SHARED_SECRET", "JWT_SECRET", "PASSWORD_HASH_SALT"):
        monkeypatch.delenv(name, raising=False)
    insecure = Settings(_env_file=None).insecure_secret_settings()
    assert set(insecure) == {"AUTOMATION_SHARED_SECRET", "JWT_SECRET", "PASSWORD_HASH_SALT"}


def test_custom_secrets_pass():
    custom = Settings(
        _env_file=None,
        automation_shared_secret="a-unique-automation-secret",
        jwt_secret="a-unique-jwt-secret-with-enough-length-123",
        password_hash_salt="a-unique-salt",
    )
    assert custom.insecure_secret_settings() == []


# ── C5: no hardcoded staff accounts ──

def test_service_has_no_builtin_users():
    from app.services.user_service import UserService

    assert UserService().in_memory_users == {}


def test_deleted_user_is_not_resurrected_from_cache(monkeypatch):
    """When the database answers "no such user", the cached copy must not be returned."""
    user_service.cache_user("ghost@glgassets.com", "Ghost", UserRole.ADMIN, "ghost-pass")

    class _Result:
        def scalars(self):
            return self

        def first(self):
            return None

    class _Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def execute(self, stmt):
            return _Result()

    monkeypatch.setattr("app.services.user_service.async_session_factory", lambda: _Session())
    assert asyncio.run(user_service.get_user_by_email("ghost@glgassets.com")) is None
    assert "ghost@glgassets.com" not in user_service.in_memory_users


# ── C6: policy simulator cannot execute code ──

def test_policy_simulator_rejects_sandbox_escape():
    escape = "().__class__.__base__.__subclasses__()"
    result = asyncio.run(control_plane_service.simulate_policy(escape, {}))
    assert result["success"] is False
    assert result["triggered"] is False


def test_policy_simulator_rejects_function_calls():
    result = asyncio.run(control_plane_service.simulate_policy("len(location) > 1", {"location": "Banani"}))
    assert result["success"] is False


# ── C7: Telegram webhook management requires admin/developer ──

def test_telegram_setup_webhook_requires_auth():
    res = client.post("/api/v1/social/telegram/setup-webhook", json={"url": "https://attacker.example/hook"})
    assert res.status_code == 401


def test_telegram_setup_webhook_rejects_viewer():
    res = client.post(
        "/api/v1/social/telegram/setup-webhook",
        json={"url": "https://attacker.example/hook"},
        headers=_bearer(UserRole.VIEWER),
    )
    assert res.status_code == 403


def test_telegram_status_requires_auth():
    assert client.get("/api/v1/social/telegram/status").status_code == 401

"""Security regression suite — one test (or more) per finding in PRINCIPAL_ENGINEER_SECURITY_REVIEW.md.

Each test pins the *fixed* behavior, so re-introducing a vulnerability fails CI.
"""

import hashlib
import hmac
import json
import time

import jwt
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.core import security
from app.core.security import create_access_token, create_stream_ticket
from app.main import app

client = TestClient(app)


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def user_token(role: str, tenant: str = "tenant-a", sub: str | None = None) -> str:
    return create_access_token({
        "sub": sub or f"usr-{role}",
        "email": f"{role}@glgassets.com",
        "role": role,
        "tenant_id": tenant,
    })


def login(email: str, password: str, headers: dict | None = None):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}, headers=headers or {})


SERVICE = {"X-Automation-Secret": settings.automation_shared_secret}


# ── F1: one secret was JWT key + admin bearer ───────────────────────────────

def test_f1_jwt_signed_with_automation_secret_is_rejected():
    forged = jwt.encode(
        {"sub": "attacker", "role": "admin", "type": "access", "sid": "x", "iat": int(time.time()),
         "exp": int(time.time()) + 3600},
        settings.automation_shared_secret,
        algorithm="HS256",
    )
    assert client.get("/api/v1/auth/users", headers=bearer(forged)).status_code == 401


def test_f1_service_secret_is_not_admin():
    assert client.get("/api/v1/auth/users", headers=SERVICE).status_code == 403
    resp = client.post("/api/v1/ai-control/policies/simulate", headers=SERVICE,
                       json={"condition_expression": "1 == 1", "context": {}})
    assert resp.status_code == 403


def test_f1_service_secret_still_reaches_automation_routes():
    resp = client.get("/api/v1/automation/daily-digest", headers=SERVICE)
    assert resp.status_code not in (401, 403)


def test_f1_bearer_takes_precedence_over_secret():
    """A viewer whose (old) client also sends the secret must be authorized as a viewer."""
    headers = {**bearer(user_token("viewer")), **SERVICE}
    assert client.get("/api/v1/auth/users", headers=headers).status_code == 403


def test_f1_publicly_known_secret_values_never_validate(monkeypatch):
    from app.dependencies import is_valid_automation_secret

    for public_value in ("glg-secret-key", "change-me-in-production", "change-me-to-a-random-secret"):
        monkeypatch.setattr(settings, "automation_shared_secret", public_value)
        assert is_valid_automation_secret(public_value) is False


def test_f1_jwt_secret_is_required(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "short")
    with pytest.raises(RuntimeError):
        security._load_signing_key()
    monkeypatch.setattr(settings, "jwt_secret", settings.automation_shared_secret + "x" * 40)
    monkeypatch.setattr(settings, "automation_shared_secret", settings.jwt_secret)
    with pytest.raises(RuntimeError):
        security._load_signing_key()


# ── F2: eval() RCE (full matrix in test_safe_expression.py) ─────────────────

def test_f2_policy_simulator_rejects_object_graph_escape():
    resp = client.post(
        "/api/v1/ai-control/policies/simulate",
        headers=bearer(user_token("developer")),
        json={"condition_expression": "().__class__.__base__.__subclasses__()", "context": {}},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is False


# ── F3: refresh token as access token; revocation not enforced ─────────────

def test_f3_refresh_token_cannot_be_used_as_bearer():
    resp = login("admin@glgassets.com", "admin123")
    refresh = resp.json()["refresh_token"]
    assert client.get("/api/v1/auth/users", headers=bearer(refresh)).status_code == 401


def test_f3_logout_revokes_the_access_token_too():
    body = login("admin@glgassets.com", "admin123").json()
    access, refresh = body["access_token"], body["refresh_token"]
    assert client.get("/api/v1/auth/users", headers=bearer(access)).status_code == 200

    client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert client.get("/api/v1/auth/users", headers=bearer(access)).status_code == 401


def test_f3_refresh_replay_kills_the_session():
    body = login("manager@glgassets.com", "manager123").json()
    old_refresh = body["refresh_token"]

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    new_access = rotated.json()["access_token"]

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401
    assert client.get("/api/v1/auth/users", headers=bearer(new_access)).status_code == 401


def test_f3_stream_ticket_is_not_an_access_token():
    ticket = create_stream_ticket({"sub": "u", "role": "admin", "sid": "s1"})
    assert client.get("/api/v1/auth/users", headers=bearer(ticket)).status_code == 401


# ── F4: unauthenticated state-changing endpoints ───────────────────────────

FORMERLY_OPEN = [
    ("GET", "/api/v1/conversations"),
    ("POST", "/api/v1/conversations"),
    ("DELETE", "/api/v1/conversations/tg_1"),
    ("GET", "/api/v1/conversations/tg_1/messages"),
    ("POST", "/api/v1/conversations/tg_1/message"),
    ("POST", "/api/v1/conversations/tg_1/takeover"),
    ("POST", "/api/v1/conversations/tg_1/reply"),
    ("GET", "/api/v1/conversations/stream"),
    ("POST", "/api/v1/social/telegram/setup-webhook"),
    ("GET", "/api/v1/social/telegram/status"),
    ("POST", "/api/v1/social/simulator/comment-to-dm"),
    ("GET", "/api/v1/automation/n8n/health"),
    ("POST", "/api/v1/automation/n8n/workflows/wf/toggle"),
    ("POST", "/api/v1/automation/n8n/workflows/wf/test"),
    ("GET", "/api/v1/developer/logs/stream"),
    ("GET", "/api/v1/email/threads"),
    ("POST", "/api/v1/email/threads/t1/approve"),
    ("POST", "/api/v1/email/threads/t1/edit-and-send"),
    ("POST", "/api/v1/email/threads/dispatch-outbound"),
    ("POST", "/api/v1/email/incoming"),
]


@pytest.mark.parametrize("method,path", FORMERLY_OPEN)
def test_f4_requires_authentication(method, path):
    resp = client.request(method, path, json={})
    assert resp.status_code == 401, f"{method} {path} -> {resp.status_code}"


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/v1/conversations"),
    ("POST", "/api/v1/conversations/tg_1/reply"),
    ("GET", "/api/v1/automation/n8n/health"),
    ("POST", "/api/v1/social/telegram/setup-webhook"),
    ("GET", "/api/v1/email/threads"),
])
def test_f4_viewer_role_is_forbidden(method, path):
    resp = client.request(method, path, json={}, headers=bearer(user_token("viewer")))
    assert resp.status_code == 403


def test_f4_email_ingest_is_service_only():
    resp = client.post("/api/v1/email/incoming", json={}, headers=bearer(user_token("admin")))
    assert resp.status_code == 403


def test_f4_websocket_requires_ticket():
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/v1/ws/chat") as ws:
            ws.receive_json()
    assert exc.value.code == 4401


def test_f4_websocket_accepts_valid_ticket():
    body = login("agent@glgassets.com", "agent123").json()
    ticket = client.post("/api/v1/auth/stream-ticket", headers=bearer(body["access_token"])).json()["ticket"]
    with client.websocket_connect(f"/api/v1/ws/chat?ticket={ticket}") as ws:
        assert ws.receive_json()["event"] == "connected"


def test_f4_stream_ticket_role_is_enforced():
    viewer_ticket = create_stream_ticket({"sub": "v", "role": "viewer", "sid": "sv"})
    assert client.get(f"/api/v1/developer/logs/stream?ticket={viewer_ticket}").status_code == 403


# ── F6: webhook authenticity ───────────────────────────────────────────────

def test_f6_meta_webhook_fails_closed_without_app_secret(monkeypatch):
    monkeypatch.setattr(settings, "facebook_app_secret", None)
    assert client.post("/api/v1/social/facebook/webhook", json={"entry": []}).status_code == 503


def test_f6_meta_webhook_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(settings, "facebook_app_secret", "meta-app-secret")
    resp = client.post("/api/v1/social/instagram/webhook", content=b'{"entry": []}',
                       headers={"X-Hub-Signature-256": "sha256=" + "0" * 64,
                                "Content-Type": "application/json"})
    assert resp.status_code == 403


def test_f6_meta_webhook_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(settings, "facebook_app_secret", "meta-app-secret")
    raw = json.dumps({"entry": []}).encode()
    sig = hmac.new(b"meta-app-secret", raw, hashlib.sha256).hexdigest()
    resp = client.post("/api/v1/social/facebook/webhook", content=raw,
                       headers={"X-Hub-Signature-256": f"sha256={sig}", "Content-Type": "application/json"})
    assert resp.status_code == 200


def test_f6_meta_subscription_has_no_default_token(monkeypatch):
    monkeypatch.setattr(settings, "whatsapp_verify_token", None)
    resp = client.get("/api/v1/social/facebook/webhook",
                      params={"hub.mode": "subscribe", "hub.verify_token": "glg_wa_verify_2026", "hub.challenge": "c"})
    assert resp.status_code == 403


def test_f6_telegram_webhook_requires_secret_header(monkeypatch):
    monkeypatch.setattr(settings, "telegram_webhook_secret", "tg-secret")
    assert client.post("/api/v1/social/telegram", json={}).status_code == 403
    ok = client.post("/api/v1/social/telegram", json={},
                     headers={"X-Telegram-Bot-Api-Secret-Token": "tg-secret"})
    assert ok.status_code == 200


# ── F7: password storage ───────────────────────────────────────────────────

def test_f7_passwords_use_salted_bcrypt():
    a, b = security.hash_password("same-password"), security.hash_password("same-password")
    assert a.startswith("$2b$") and a != b
    assert security.verify_password("same-password", a)
    assert not security.verify_password("wrong", a)


def test_f7_legacy_hashes_verify_and_are_flagged_for_upgrade():
    legacy = security._legacy_hash("old-password")
    assert security.verify_password("old-password", legacy)
    assert security.password_needs_rehash(legacy)
    assert not security.password_needs_rehash(security.hash_password("x"))


# ── F8: tenant lost on refresh ─────────────────────────────────────────────

def test_f8_tenant_survives_refresh():
    body = login("agent@glgassets.com", "agent123").json()
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]}).json()
    claims = jwt.decode(rotated["access_token"], options={"verify_signature": False})
    assert claims["tenant_id"] == "glg-default"


# ── F9: account-lockout DoS ────────────────────────────────────────────────

def test_f9_attacker_cannot_lock_victim_out_from_another_ip(monkeypatch):
    monkeypatch.setattr(settings, "client_ip_header", "X-Test-Client-IP")
    attacker = {"X-Test-Client-IP": "203.0.113.66"}
    victim = {"X-Test-Client-IP": "198.51.100.7"}

    for _ in range(6):
        login("viewer@glgassets.com", "wrong-password", attacker)
    assert login("viewer@glgassets.com", "wrong-password", attacker).status_code == 423
    assert login("viewer@glgassets.com", "viewer123", victim).status_code == 200


def test_f9_forwarded_for_is_not_trusted_by_default():
    """With no trusted proxy configured, X-Forwarded-For cannot pick a new lockout bucket."""
    for i in range(6):
        login("developer@glgassets.com", "wrong", {"X-Forwarded-For": f"10.0.0.{i}"})
    assert login("developer@glgassets.com", "dev123", {"X-Forwarded-For": "10.9.9.9"}).status_code == 423
    from app.core.account_lockout import account_lockout
    import asyncio
    asyncio.run(account_lockout.unlock_account("developer@glgassets.com"))


# ── Cookie CSRF ────────────────────────────────────────────────────────────

def test_cookie_refresh_requires_client_header():
    fresh = TestClient(app)
    fresh.post("/api/v1/auth/login", json={"email": "admin@glgassets.com", "password": "admin123"})
    assert fresh.post("/api/v1/auth/refresh").status_code == 403
    ok = fresh.post("/api/v1/auth/refresh", headers={"X-GLG-Client": "dashboard"})
    assert ok.status_code == 200


# ── Knowledge path traversal (CWE-22) ──────────────────────────────────────

@pytest.mark.parametrize("doc_id", ["../../evil", "/etc/cron.d/x", "a/b", ".."])
def test_knowledge_doc_id_cannot_escape_base_dir(doc_id):
    resp = client.post(
        "/api/v1/knowledge/upload",
        headers=bearer(user_token("admin")),
        files={"file": ("x.txt", b"hello world", "text/plain")},
        data={"doc_id": doc_id},
    )
    assert resp.status_code == 400

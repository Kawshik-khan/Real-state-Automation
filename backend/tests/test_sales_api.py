"""Sales API and channel webhooks over HTTP."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from sales_fixtures import add_daily_slots

from app.config import settings
from app.core.security import create_access_token
from app.main import app
from app.sales.db import session_scope


@pytest.fixture
def client(db, project):
    with TestClient(app) as c:
        yield c


def headers(role: str, sub: str = "user-1") -> dict:
    token = create_access_token({"sub": sub, "role": role, "tenant_id": settings.default_tenant_id, "email": f"{sub}@glg.com"})
    return {"Authorization": f"Bearer {token}"}


MANAGER = headers("manager", "manager-1")
AGENT = headers("agent", "agent-1")
VIEWER = headers("viewer", "viewer-1")


def test_inventory_permissions_and_stale_edits(client):
    body = {"project_id": "proj_gulshan", "unit_code": "C-3", "list_price_bdt": 12_500_000, "bedrooms": 3}
    assert client.post("/api/v1/sales/units", json=body, headers=AGENT).status_code == 403
    created = client.post("/api/v1/sales/units", json=body, headers=MANAGER)
    assert created.status_code == 201, created.text
    unit = created.json()["unit"]
    listed = client.get("/api/v1/sales/units", headers=VIEWER).json()["units"]
    assert [u["unit_code"] for u in listed] == ["C-3"]

    edit = client.patch(f"/api/v1/sales/units/{unit['unit_id']}", json={"version": unit["version"], "status": "SOLD"}, headers=MANAGER)
    assert edit.status_code == 200 and edit.json()["unit"]["status"] == "SOLD"
    stale = client.patch(f"/api/v1/sales/units/{unit['unit_id']}", json={"version": unit["version"], "notes": "x"}, headers=MANAGER)
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_VERSION"
    bad = client.post("/api/v1/sales/units", json={**body, "project_id": "nope"}, headers=MANAGER)
    assert bad.status_code == 404 and bad.json()["code"] == "PROJECT_NOT_FOUND"


def test_lead_workflow_over_http(client):
    created = client.post("/api/v1/sales/leads", json={"name": "Walk-in Rina", "phone": "01711-000123", "budget_max_bdt": 9_000_000, "preferred_areas": ["Banani"]}, headers=AGENT)
    assert created.status_code == 201, created.text
    lead = created.json()["lead"]
    assert lead["phone"] == "+8801711000123" and lead["stage"] == "QUALIFIED"

    detail = client.get(f"/api/v1/sales/leads/{lead['lead_id']}", headers=VIEWER).json()
    assert detail["conversation"]["channel"] == "whatsapp" and detail["events"]

    assert client.post(f"/api/v1/sales/leads/{lead['lead_id']}/stage", json={"stage": "NEGOTIATING"}, headers=VIEWER).status_code == 403
    moved = client.post(f"/api/v1/sales/leads/{lead['lead_id']}/stage", json={"stage": "NEGOTIATING"}, headers=AGENT)
    assert moved.status_code == 200 and moved.json()["lead"]["stage"] == "NEGOTIATING"
    lost = client.post(f"/api/v1/sales/leads/{lead['lead_id']}/stage", json={"stage": "LOST"}, headers=AGENT)
    assert lost.status_code == 400 and lost.json()["code"] == "LOST_REASON_REQUIRED"

    assert client.post(f"/api/v1/sales/leads/{lead['lead_id']}/notes", json={"text": "Prefers south facing"}, headers=AGENT).status_code == 201
    overview = client.get("/api/v1/sales/overview", headers=VIEWER).json()
    assert overview["pipeline"]["NEGOTIATING"] == 1 and overview["assistant"]["mode"] == "shadow"


def test_staff_can_book_and_complete_a_visit(client, sent):
    import asyncio

    asyncio.run(add_daily_slots(tenant=settings.default_tenant_id))
    lead = client.post("/api/v1/sales/leads", json={"name": "Kamal", "phone": "01811000999"}, headers=AGENT).json()["lead"]
    free = client.get("/api/v1/sales/visit-slots/free", params={"project_id": "proj_gulshan"}, headers=AGENT).json()["slots"]
    booked = client.post(f"/api/v1/sales/leads/{lead['lead_id']}/visits", json={"project_id": "proj_gulshan", "slot_start": free[0]["slot_start"]}, headers=AGENT)
    assert booked.status_code == 201, booked.text
    visit = booked.json()["visit"]
    done = client.patch(f"/api/v1/sales/visits/{visit['visit_id']}", json={"status": "DONE", "notes": "liked 5th floor"}, headers=AGENT)
    assert done.status_code == 200 and done.json()["visit"]["status"] == "DONE"
    detail = client.get(f"/api/v1/sales/leads/{lead['lead_id']}", headers=AGENT).json()
    assert detail["lead"]["stage"] == "VISITED"


def test_approval_decisions_are_for_managers(client):
    import asyncio

    from app.sales import approvals, leads

    unit = client.post("/api/v1/sales/units", json={"project_id": "proj_gulshan", "unit_code": "D-1", "list_price_bdt": 9_900_000}, headers=MANAGER).json()["unit"]

    async def raise_request():
        async with session_scope() as s:
            lead, _ = await leads.get_or_create_lead(s, settings.default_tenant_id, "telegram", "t-1", name="Asif")
            return await approvals.request_unit_hold(s, lead, unit["unit_id"], "2 days", "ai")

    request = asyncio.run(raise_request())
    pending = client.get("/api/v1/sales/approvals", headers=AGENT).json()["approvals"]
    assert [p["approval_id"] for p in pending] == [request["approval_id"]]
    url = f"/api/v1/sales/approvals/{request['approval_id']}/decision"
    assert client.post(url, json={"decision": "APPROVED"}, headers=AGENT).status_code == 403
    decided = client.post(url, json={"decision": "APPROVED", "reason": "deposit promised"}, headers=MANAGER)
    assert decided.status_code == 200 and decided.json()["approval"]["unit_status_now"] == "HELD"
    again = client.post(url, json={"decision": "REJECTED"}, headers=MANAGER)
    assert again.status_code == 409


def test_settings_and_sequences(client):
    assert client.patch("/api/v1/sales/settings", json={"mode": "live"}, headers=AGENT).status_code == 403
    updated = client.patch("/api/v1/sales/settings", json={"mode": "live", "enabled_channels": ["whatsapp", "telegram"]}, headers=MANAGER)
    assert updated.json()["settings"]["mode"] == "live"
    bad = client.patch("/api/v1/sales/settings", json={"enabled_channels": ["fax"]}, headers=MANAGER)
    assert bad.status_code == 400
    installed = client.post("/api/v1/sales/sequences/install-defaults", headers=MANAGER).json()["created"]
    assert {s["trigger"] for s in installed} == {"new_lead", "post_visit", "no_show", "reengage"}
    edited = client.put("/api/v1/sales/sequences/new_lead", json={"name": "Short", "steps": [{"delay_minutes": 60, "message_template": "Hi {name}"}]}, headers=MANAGER)
    assert edited.status_code == 200 and len(edited.json()["sequence"]["steps"]) == 1


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_meta_webhook_requires_a_valid_signature(client, monkeypatch):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {
            "contacts": [{"wa_id": "8801712345678", "profile": {"name": "Sadia"}}],
            "messages": [{"from": "8801712345678", "id": "wamid.ABC", "type": "text", "text": {"body": "Banani te flat?"}}],
        }}]}],
    }
    raw = json.dumps(payload).encode()
    monkeypatch.setattr(settings, "facebook_app_secret", None)
    assert client.post("/api/v1/sales/webhooks/meta", content=raw).status_code == 503
    monkeypatch.setattr(settings, "facebook_app_secret", "app-secret")
    assert client.post("/api/v1/sales/webhooks/meta", content=raw, headers={"X-Hub-Signature-256": _sign(raw, "wrong")}).status_code == 401
    ok = client.post("/api/v1/sales/webhooks/meta", content=raw, headers={"X-Hub-Signature-256": _sign(raw, "app-secret")})
    assert ok.status_code == 200 and ok.json()["results"][0]["new_lead"] is True
    repeat = client.post("/api/v1/sales/webhooks/meta", content=raw, headers={"X-Hub-Signature-256": _sign(raw, "app-secret")})
    assert repeat.json()["results"][0]["status"] == "duplicate"
    leads = client.get("/api/v1/sales/leads", headers=AGENT).json()["leads"]
    assert leads[0]["name"] == "Sadia" and leads[0]["phone"] == "+8801712345678"


def test_meta_verification_and_telegram_secret(client, monkeypatch):
    monkeypatch.setattr(settings, "whatsapp_verify_token", "verify-me")
    ok = client.get("/api/v1/sales/webhooks/meta", params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "42"})
    assert ok.text == "42"
    assert client.get("/api/v1/sales/webhooks/meta", params={"hub.mode": "subscribe", "hub.verify_token": "x"}).status_code == 403

    update = {"message": {"message_id": 7, "chat": {"id": 991, "type": "private"}, "from": {"first_name": "Tanvir"}, "text": "price?"}}
    monkeypatch.setattr(settings, "telegram_webhook_secret", "tg-secret")
    assert client.post("/api/v1/sales/webhooks/telegram", json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "bad"}).status_code == 401
    accepted = client.post("/api/v1/sales/webhooks/telegram", json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "tg-secret"})
    assert accepted.json()["result"]["status"] == "accepted"
    group = {"message": {"message_id": 8, "chat": {"id": -5, "type": "group"}, "text": "hi"}}
    assert client.post("/api/v1/sales/webhooks/telegram", json=group, headers={"X-Telegram-Bot-Api-Secret-Token": "tg-secret"}).json() == {"received": 0}


def test_website_widget_round_trip(client, sent):
    secret = {"X-Automation-Secret": settings.automation_shared_secret}
    sent_msg = client.post("/api/v1/sales/webhooks/website", json={"session_id": "visitor-123456", "text": "Hello", "message_id": "w-1"}, headers=secret)
    assert sent_msg.status_code == 200 and sent_msg.json()["status"] == "accepted"
    conv_id = sent_msg.json()["conversation_id"]
    reply = client.post(f"/api/v1/sales/conversations/{conv_id}/reply", json={"text": "Hi! How can I help?"}, headers=AGENT)
    assert reply.json()["message"]["status"] == "stored" and reply.json()["conversation"]["mode"] == "HUMAN"
    pulled = client.get("/api/v1/sales/webhooks/website/visitor-123456/messages", headers=secret).json()["messages"]
    assert [m["text"] for m in pulled] == ["Hi! How can I help?"]
    assert client.post("/api/v1/sales/webhooks/website", json={"session_id": "visitor-123456", "text": "x"}).status_code == 401


def test_ai_quality_shadow_ratings_and_channel_modes_over_http(client):
    from app.sales.models import AIShadowPair

    async def seed():
        async with session_scope() as s:
            s.add(AIShadowPair(tenant_id=settings.default_tenant_id, legacy_conversation_id="w1", channel="website",
                               customer_text="Gulshan e flat?", legacy_reply="old", sales_reply="new", sales_outcome="drafted"))

    client.portal.call(seed)
    pairs = client.get("/api/v1/sales/shadow/pairs?rated=false", headers=VIEWER).json()["pairs"]
    assert len(pairs) == 1
    assert client.post(f"/api/v1/sales/shadow/pairs/{pairs[0]['pair_id']}/rating", json={"rating": "better"}, headers=VIEWER).status_code == 403
    rated = client.post(f"/api/v1/sales/shadow/pairs/{pairs[0]['pair_id']}/rating", json={"rating": "better", "note": "clearer"}, headers=AGENT)
    assert rated.status_code == 200 and rated.json()["pair"]["rating"] == "better"

    quality = client.get("/api/v1/sales/ai-quality", headers=VIEWER).json()
    assert quality["comparison"]["better"] == 1 and quality["routing"]["ai_route_via_sales"] == "legacy"
    assert quality["ready_to_retire_legacy"] is False

    assert client.patch("/api/v1/sales/settings", json={"channel_modes": {"email": "live"}}, headers=AGENT).status_code == 403
    changed = client.patch("/api/v1/sales/settings", json={"channel_modes": {"email": "live", "website": "draft_only"}}, headers=MANAGER)
    assert changed.status_code == 200 and changed.json()["settings"]["channel_modes"]["website"] == "draft_only"
    assert client.patch("/api/v1/sales/settings", json={"channel_modes": {"email": "maybe"}}, headers=MANAGER).status_code == 422

    run = client.post("/api/v1/sales/content/drafts/run", headers=MANAGER)
    assert run.status_code == 200 and run.json() == {"created": [], "skipped_pending": []}

"""/api/v1/ads control endpoints and the Meta leadgen webhook."""

import hashlib
import hmac
import json

import pytest
from ads_fakes import FakeAdsRepository
from fastapi.testclient import TestClient

import app.api.v1.ads.endpoints as ads_endpoints
import app.api.v1.social.endpoints as social_endpoints
from app.core.security import create_access_token
from app.main import app
from app.services.ads.meta_leads import parse_lead, verify_signature

client = TestClient(app)


def _headers(role: str) -> dict:
    return {"Authorization": "Bearer " + create_access_token({
        "sub": f"{role}@glgassets.com", "email": f"{role}@glgassets.com", "role": role, "tenant_id": "glg-assets-test"})}


def test_status_lists_platforms_without_secrets():
    body = client.get("/api/v1/ads/status", headers=_headers("manager")).json()
    assert body["success"] is True
    assert {p["platform"] for p in body["platforms"]} == {"meta", "google_ads", "tiktok"}
    assert all(p["configured"] is False for p in body["platforms"])
    assert "access_token" not in json.dumps(body)


def test_sync_requires_operator_role_and_configuration(monkeypatch):
    assert client.post("/api/v1/ads/sync", json={}, headers=_headers("agent")).status_code == 403
    assert client.post("/api/v1/ads/sync", json={}, headers=_headers("manager")).status_code == 503
    monkeypatch.setattr(ads_endpoints, "get_ads_repository", lambda: FakeAdsRepository())
    res = client.post("/api/v1/ads/sync", json={"lookback_days": 7}, headers=_headers("manager"))
    assert res.status_code == 409  # no credentials configured
    assert client.post("/api/v1/ads/sync", json={"lookback_days": 400}, headers=_headers("manager")).status_code == 422


def test_fx_rate_admin_only(monkeypatch):
    fake = FakeAdsRepository()
    monkeypatch.setattr(ads_endpoints, "get_ads_repository", lambda: fake)
    assert client.put("/api/v1/ads/fx-rates", json={"currency": "USD", "rate_to_bdt": 122.5}, headers=_headers("manager")).status_code == 403
    assert client.put("/api/v1/ads/fx-rates", json={"currency": "usd", "rate_to_bdt": 122.5}, headers=_headers("admin")).status_code == 200
    assert fake.fx_rates[0]["currency"] == "USD" and fake.fx_rates[0]["rate_to_bdt"] == 122.5


def test_signature_verification():
    body = b'{"entry": []}'
    good = "sha256=" + hmac.new(b"appsecret", body, hashlib.sha256).hexdigest()
    assert verify_signature(body, good, "appsecret")
    assert not verify_signature(body, "sha256=deadbeef", "appsecret")
    assert not verify_signature(body, None, "appsecret")
    assert verify_signature(body, None, None)  # not configured → accepted (legacy behaviour)


def test_facebook_webhook_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(social_endpoints.settings, "facebook_app_secret", "appsecret")
    payload = json.dumps({"entry": []}).encode()
    bad = client.post("/api/v1/social/facebook/webhook", content=payload,
                      headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=00"})
    assert bad.status_code == 403
    sig = "sha256=" + hmac.new(b"appsecret", payload, hashlib.sha256).hexdigest()
    ok = client.post("/api/v1/social/facebook/webhook", content=payload,
                     headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig})
    assert ok.status_code == 200


def test_leadgen_event_triggers_ingestion(monkeypatch):
    monkeypatch.setattr(social_endpoints.settings, "facebook_app_secret", None)
    received = []

    async def fake_ingest(leadgen_id):
        received.append(leadgen_id)
    monkeypatch.setattr(social_endpoints, "ingest_leadgen", fake_ingest)
    res = client.post("/api/v1/social/facebook/webhook", json={"entry": [{"changes": [
        {"field": "leadgen", "value": {"leadgen_id": "4455", "form_id": "f1", "ad_id": "a1", "page_id": "p1"}}]}]})
    assert res.status_code == 200
    assert received == ["4455"]


@pytest.mark.parametrize("fields,name,contact", [
    ([{"name": "full_name", "values": ["Rahim Uddin"]}, {"name": "phone_number", "values": ["+8801700000000"]}],
     "Rahim Uddin", "+8801700000000"),
    ([{"name": "first_name", "values": ["Nusrat"]}, {"name": "last_name", "values": ["Jahan"]},
      {"name": "email", "values": ["n@example.com"]}], "Nusrat Jahan", "n@example.com"),
])
def test_parse_lead(fields, name, contact):
    row = parse_lead({"id": "99", "created_time": "2026-09-27T08:00:00+0000", "field_data": fields,
                      "campaign_id": "c1", "ad_id": "a1", "form_id": "f1"}, "glg-assets-test")
    assert row["lead_id"] == "meta:99" and row["name"] == name and row["contact"] == contact
    assert (row["external_campaign_id"], row["external_ad_id"], row["source"]) == ("c1", "a1", "meta_lead_ad")

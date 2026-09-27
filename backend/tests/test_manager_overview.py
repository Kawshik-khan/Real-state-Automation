"""Manager overview endpoint: same synced numbers as /social-kpis plus tours and approvals."""

from datetime import timedelta

import pytest
from ads_fakes import FakeAdsRepository
from fastapi.testclient import TestClient

import app.api.v1.analytics.endpoints as analytics_endpoints
from app.core.security import create_access_token
from app.main import app
from app.services.ads.sync_service import reporting_today

client = TestClient(app)
URL = "/api/v1/analytics/manager-overview"
HEADERS = {"Authorization": "Bearer " + create_access_token({
    "sub": "manager@glgassets.com", "email": "manager@glgassets.com", "role": "manager", "tenant_id": "glg-assets-test"})}


@pytest.fixture
def repo(monkeypatch):
    fake = FakeAdsRepository()
    monkeypatch.setattr(analytics_endpoints, "get_ads_repository", lambda: fake)
    return fake


def test_unconfigured():
    body = client.get(URL, headers=HEADERS).json()
    assert body["data_source"] == "unconfigured"


def test_empty_database_has_no_invented_defaults(repo):
    body = client.get(URL, headers=HEADERS).json()
    assert body["data_source"] == "empty"
    k = body["kpis"]
    # Old implementation defaulted to 5 pending posts, 32 tours, 142 conversations and 96.8% answered.
    assert k["pending_social_posts"] == 0
    assert k["confirmed_tours"] == 0
    assert k["ai_response_rate_pct"] is None
    assert k["total_ad_spend_bdt"] == 0 and body["campaigns"] == []
    assert len(k["leads_vs_tours"]) == 4


def test_tours_pending_posts_and_ai_sla_come_from_tables(repo):
    today = reporting_today()
    repo.pending_posts = 3
    repo.bookings = [
        {"id": "b1", "status": "confirmed", "tour_date": (today - timedelta(days=2)).isoformat()},
        {"id": "b2", "status": "pending", "tour_date": (today - timedelta(days=2)).isoformat()},
        {"id": "b3", "status": "completed", "tour_date": (today - timedelta(days=60)).isoformat()},
    ]
    repo.milestones = [{"id": "m1", "status": "confirmed", "milestone_date": (today - timedelta(days=1)).isoformat()}]
    start = f"{(today - timedelta(days=1)).isoformat()}T09:00:00+00:00"
    repo.conversations = [{"conversation_id": "x", "channel": "whatsapp", "created_at": start}]
    repo.messages = [
        {"conversation_id": "x", "sender": "user", "created_at": start},
        {"conversation_id": "x", "sender": "ai", "created_at": start.replace("09:00:00", "09:00:02")},
    ]
    k = client.get(URL, headers=HEADERS).json()["kpis"]
    assert k["pending_social_posts"] == 3
    assert k["confirmed_tours"] == 2  # confirmed booking + tour milestone; pending/old excluded
    assert k["ai_response_rate_pct"] == 100.0
    assert k["ai_median_first_reply_seconds"] == 2.0
    assert k["ai_inbound_conversations"] == 1

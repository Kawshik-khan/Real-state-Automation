"""Social Media KPI & Campaign Command Center endpoint: real synced data only, no fallbacks."""

from datetime import date, timedelta

import pytest
from ads_fakes import FakeAdsRepository, FakeConnector
from fastapi.testclient import TestClient

import app.api.v1.analytics.endpoints as analytics_endpoints
from app.core.security import create_access_token
from app.main import app
from app.models.user import UserRole
from app.services.ads.factory import ConnectorSpec
from app.services.ads.sync_service import reporting_today, sync_all
from app.services.ads.types import AdAccount, Campaign, DailyMetric, PeriodReach, SyncPayload

client = TestClient(app)
URL = "/api/v1/analytics/social-kpis"


def _headers(role: str) -> dict:
    token = create_access_token({"sub": f"{role}@glgassets.com", "email": f"{role}@glgassets.com", "role": role,
                                 "tenant_id": "glg-assets-test"})
    return {"Authorization": f"Bearer {token}"}


MANAGER = _headers(UserRole.MANAGER.value)


@pytest.fixture
def repo(monkeypatch):
    fake = FakeAdsRepository()
    monkeypatch.setattr(analytics_endpoints, "get_ads_repository", lambda: fake)
    return fake


async def _seed_via_sync(repo: FakeAdsRepository) -> date:
    today = reporting_today()
    account = AdAccount("meta", "111", "GLG", "BDT")
    payload = SyncPayload(
        account=account,
        campaigns=[Campaign("meta", "c1", account.id, "GLG Sky Tower Leads", "ACTIVE", "OUTCOME_LEADS", "lead_generation", "BDT")],
        daily_metrics=[
            DailyMetric("meta", "c1", today - timedelta(days=1), "facebook", account.id, "BDT", impressions=10000,
                        clicks=300, spend=5000, leads=10, messaging_conversations=4),
            DailyMetric("meta", "c1", today - timedelta(days=2), "instagram", account.id, "BDT", impressions=4000,
                        clicks=100, spend=2000, leads=4),
            DailyMetric("meta", "c1", today - timedelta(days=40), "facebook", account.id, "BDT", impressions=999,
                        spend=999, leads=99),  # falls in the previous 30-day window only
        ],
        period_reach=[PeriodReach("meta", "__account__", 30, today - timedelta(days=29), today, 9000)],
    )
    await sync_all(repo, [ConnectorSpec("meta", "111", FakeConnector(payload))], trigger="manual", lookback_days=90, today=today)
    return today


def test_unconfigured_backend_says_so_instead_of_inventing_numbers():
    # CI has SUPABASE_URL="" so the real factory returns no repository.
    res = client.get(URL, headers=MANAGER)
    assert res.status_code == 200
    body = res.json()
    assert body["data_source"] == "unconfigured"
    assert "kpis" not in body


def test_requires_authentication_and_dashboard_role(repo):
    assert client.get(URL).status_code == 401
    assert client.get(URL, headers=_headers(UserRole.DEVELOPER.value)).status_code == 403
    for role in (UserRole.MANAGER, UserRole.ADMIN, UserRole.AGENT, UserRole.VIEWER):
        assert client.get(URL, headers=_headers(role.value)).status_code == 200


def test_empty_database_returns_empty_not_seed_numbers(repo):
    body = client.get(URL, headers=MANAGER).json()
    assert body["data_source"] == "empty"
    assert body["demo_available"] is False
    assert body["kpis"]["leads"] == 0 and body["kpis"]["cpl_bdt"] is None
    assert body["campaigns"] == [] and body["posts"] == []


def test_demo_rows_only_on_request(repo):
    repo.demo_campaigns = [{"id": "u1", "platform": "facebook", "campaign_name": "Seed", "campaign_type": "lead_generation",
                            "ad_spend_bdt": 425000, "impressions": 540000, "reach": 420000, "engagements": 32400,
                            "leads_generated": 268, "is_demo": True}]
    plain = client.get(URL, headers=MANAGER).json()
    assert plain["data_source"] == "empty" and plain["demo_available"] is True
    demo = client.get(URL, params={"include_demo": "true"}, headers=MANAGER).json()
    assert demo["data_source"] == "demo" and demo["kpis"]["leads"] == 268


async def test_synced_rows_flow_to_dashboard_with_real_periods(repo):
    await _seed_via_sync(repo)
    body = client.get(URL, params={"period": "30d"}, headers=MANAGER).json()
    assert body["data_source"] == "live"
    assert body["last_synced_at"]
    k = body["kpis"]
    assert (k["leads"], k["impressions"], k["spend_bdt"]) == (14, 14000, 7000)
    assert k["cpl_bdt"] == 500.0
    assert k["reach"] == 9000 and body["reach_method"] == "account_dedup"
    assert body["deltas"]["leads"] == pytest.approx(round((14 - 99) / 99 * 100, 1))
    assert [c["id"] for c in body["platforms"]] == ["facebook", "instagram"]
    assert body["campaigns"][0]["name"] == "GLG Sky Tower Leads"

    week = client.get(URL, params={"period": "7d", "platform": "instagram"}, headers=MANAGER).json()
    assert week["kpis"]["leads"] == 4 and len(week["time_series"]) == 7
    assert week["period"]["days"] == 7


def test_campaign_status_is_read_only():
    res = client.patch("/api/v1/analytics/campaigns/cmp-004/status", json={"status": "ACTIVE"},
                       headers={"X-Automation-Secret": analytics_endpoints.settings.automation_shared_secret})
    assert res.status_code == 409
    assert "ad platform" in res.json()["detail"]

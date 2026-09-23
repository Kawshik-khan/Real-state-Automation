"""Automated integration tests for Manager Overview Dashboard API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)
HEADERS = {"X-Automation-Secret": settings.automation_shared_secret}


class TestManagerOverviewEndpoints:
    def test_get_manager_overview_success(self):
        """GET /api/v1/analytics/manager-overview returns valid 200 and complete KPI structure."""
        response = client.get("/api/v1/analytics/manager-overview", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "kpis" in data
        assert "campaigns" in data

        kpis = data["kpis"]
        # Verify all 6 KPI cards are present with formatted & numeric data
        assert "total_ad_spend" in kpis
        assert "total_ad_spend_num" in kpis
        assert "ad_spend_trend" in kpis
        assert len(kpis["ad_spend_trend"]) == 6

        assert "total_reach" in kpis
        assert "total_impressions" in kpis

        assert "messages_received" in kpis
        assert "cost_per_message" in kpis

        assert "ai_response_rate" in kpis
        assert "avg_ai_response_time" in kpis

        assert "qualified_leads" in kpis
        assert "confirmed_tours" in kpis
        assert "tour_conversion_rate" in kpis
        assert "leads_vs_tours_trend" in kpis
        assert len(kpis["leads_vs_tours_trend"]) == 4

        assert "pending_social_posts_count" in kpis

    def test_campaigns_list_structure(self):
        """GET /api/v1/analytics/manager-overview returns campaigns with real-time operational fields."""
        response = client.get("/api/v1/analytics/manager-overview", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        campaigns = data["campaigns"]
        assert isinstance(campaigns, list)
        assert len(campaigns) >= 4

        for cmp in campaigns:
            assert "id" in cmp
            assert "name" in cmp
            assert "platform" in cmp
            assert "spent" in cmp
            assert "reach" in cmp
            assert "messages" in cmp
            assert "leads" in cmp
            assert "cpl" in cmp
            assert "status" in cmp
            assert cmp["status"] in ["ACTIVE", "PAUSED", "OPTIMIZING"]

    def test_update_campaign_status(self):
        """PATCH /api/v1/analytics/campaigns/{id}/status toggles campaign state."""
        response = client.patch(
            "/api/v1/analytics/campaigns/cmp-004/status",
            json={"status": "ACTIVE"},
            headers=HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["campaign_id"] == "cmp-004"
        assert data["status"] == "ACTIVE"

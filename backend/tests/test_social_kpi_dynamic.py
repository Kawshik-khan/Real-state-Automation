"""Automated integration tests for dynamic, database-driven Social Media KPI & Campaign Command Center."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)
HEADERS = {"X-Automation-Secret": settings.automation_shared_secret}


class TestDynamicSocialKpis:
    def test_get_social_kpis_default(self):
        """GET /api/v1/analytics/social-kpis with default params returns dynamic DB data."""
        response = client.get("/api/v1/analytics/social-kpis?period=30d&platform=all", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data.get("is_live_db") is True
        assert "kpis" in data
        assert "platforms" in data
        assert "campaigns" in data
        assert "posts" in data
        assert "ai_recommendations" in data

        kpis = data["kpis"]
        assert kpis["total_impressions"] > 0
        assert kpis["total_reach"] > 0
        assert kpis["total_engagements"] > 0
        assert kpis["total_leads_generated"] > 0
        assert kpis["total_ad_spend"] > 0
        assert "cost_per_lead" in kpis
        assert "click_through_rate" in kpis
        assert "pipeline_roas" in kpis
        assert "pipeline_value_usd" in kpis

        # Platforms verification
        platforms = data["platforms"]
        assert len(platforms) >= 5
        platform_ids = [p["id"] for p in platforms]
        for expected in ["facebook", "instagram", "linkedin", "youtube", "tiktok"]:
            assert expected in platform_ids

        # Check Facebook platform fields
        fb = next(p for p in platforms if p["id"] == "facebook")
        assert fb["reach"] > 0
        assert fb["leads"] > 0
        assert fb["ad_spend"] > 0
        assert "cpl" in fb

        # Posts verification
        posts = data["posts"]
        assert len(posts) >= 5
        for post in posts:
            assert "id" in post
            assert "title" in post
            assert "project" in post
            assert "platform" in post
            assert "views" in post
            assert "likes" in post
            assert "comments" in post
            assert "leads_generated" in post

    def test_filter_by_platform_facebook(self):
        """Filtering by platform=facebook isolates Facebook metrics."""
        response = client.get("/api/v1/analytics/social-kpis?period=30d&platform=facebook", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # Platforms should only contain Facebook or have Facebook as the primary focus
        for p in data["platforms"]:
            assert p["id"] == "facebook"

        # Posts should be filtered to facebook
        for post in data["posts"]:
            assert post["platform"] == "facebook"

    def test_filter_by_project(self):
        """Filtering by project_id isolates matching campaigns and posts."""
        response = client.get("/api/v1/analytics/social-kpis?period=30d&project_id=proj_101", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "kpis" in data
        assert len(data["campaigns"]) >= 1

    def test_period_multiplier(self):
        """Verify 7d period recalculates KPIs dynamically."""
        res_30d = client.get("/api/v1/analytics/social-kpis?period=30d", headers=HEADERS).json()
        res_7d = client.get("/api/v1/analytics/social-kpis?period=7d", headers=HEADERS).json()

        assert res_7d["success"] is True
        # 7d impressions should be proportionally scaled from 30d
        assert res_7d["kpis"]["total_impressions"] < res_30d["kpis"]["total_impressions"]

"""Automated Unit and Integration Tests for Scheduled Report Generation and Delivery."""

import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app
from app.persistence.report_store import report_store
from app.services.report_builder import report_builder
from app.services.report_scheduler import report_scheduler
from app.services.whatsapp_dispatcher import clean_phone_number, whatsapp_dispatcher

client = TestClient(app)
AUTH_HEADERS = {"X-Automation-Secret": settings.automation_shared_secret}


class TestReportBuilderAndFormatters:
    @pytest.mark.asyncio
    async def test_gather_live_metrics_structure(self):
        """Verify metric aggregator aggregates all channels, manager ops, and campaigns."""
        metrics = await report_builder.gather_live_metrics(period_days=1)
        assert "total_inquiries" in metrics
        assert "ai_resolution_rate" in metrics
        assert "channels" in metrics
        assert "whatsapp" in metrics["channels"]
        assert "manager_operations" in metrics
        assert "marketing_campaigns" in metrics
        assert "system_health" in metrics

    def test_synthesize_insights(self):
        """Verify executive AI synthesizer produces valid takeaways and recommendations."""
        dummy_metrics = {
            "total_inquiries": 50,
            "ai_resolution_rate": 88.0,
            "site_visits_booked": 10,
            "hot_leads_count": 12,
            "channels": {"whatsapp": 30, "facebook": 12, "instagram": 8},
            "manager_operations": {"pending_review_emails": 2},
        }
        insights = report_builder.synthesize_insights(dummy_metrics)
        assert "summary" in insights
        assert "takeaways" in insights
        assert len(insights["takeaways"]) >= 2
        assert "recommendations" in insights
        assert len(insights["recommendations"]) >= 1

    def test_multi_channel_renderers(self):
        """Verify HTML, Telegram, and WhatsApp formatting render correctly."""
        dummy_metrics = {
            "period_label": "Today",
            "total_inquiries": 45,
            "ai_resolution_rate": 89.2,
            "site_visits_booked": 8,
            "hot_leads_count": 15,
            "channels": {"whatsapp": 25, "instagram": 12, "facebook": 8},
            "manager_operations": {"pending_review_emails": 3},
        }
        insights = {
            "summary": "Operating smoothly across all channels.",
            "takeaways": ["Takeaway 1", "Takeaway 2"],
            "recommendations": ["Recommendation 1"],
        }

        # 1. HTML Email
        html = report_builder.render_html_report(dummy_metrics, insights, "Daily Executive Pulse", "Alex Mercer")
        assert "GLG ASSETS REAL ESTATE AI OS" in html
        assert "Alex Mercer" in html
        assert "89.2%" in html
        assert "Takeaway 1" in html

        # 2. Telegram Markdown
        tg = report_builder.render_telegram_report(dummy_metrics, insights, "Daily Executive Pulse", "Sarah Connor")
        assert "GLG ASSETS" in tg
        assert "Sarah Connor" in tg
        assert "89.2%" in tg
        assert "WhatsApp" in tg

        # 3. WhatsApp Text
        wa = report_builder.render_whatsapp_report(dummy_metrics, insights, "Daily Executive Pulse", "Sarah Connor")
        assert "*GLG Assets" in wa
        assert "89.2%" in wa
        assert "Incoming Inquiries" in wa


class TestWhatsAppDispatcher:
    def test_clean_phone_number(self):
        """Verify phone number cleaning and international prefixing."""
        assert clean_phone_number("01712345678") == "+8801712345678"
        assert clean_phone_number("+880 1712-345678") == "+8801712345678"
        assert clean_phone_number("8801712345678") == "+8801712345678"
        assert clean_phone_number("+1 (555) 123-4567") == "+15551234567"

    @pytest.mark.asyncio
    async def test_send_executive_brief_fallback(self):
        """Verify dispatcher falls back gracefully in development and returns success."""
        res = await whatsapp_dispatcher.send_executive_brief(
            phone_number="+8801700000001",
            message_text="Test WhatsApp Executive Briefing",
        )
        assert res["success"] is True
        assert res["status"] in ("sent", "simulated")
        assert "+8801700000001" in res["target"]


class TestReportStoreAndScheduler:
    @pytest.mark.asyncio
    async def test_default_schedules_seeded(self):
        """Verify report store seeds default Daily and Weekly schedules."""
        schedules = await report_store.get_all_schedules()
        assert len(schedules) >= 2
        sched_ids = [s["id"] for s in schedules]
        assert "sched-daily-pulse" in sched_ids
        assert "sched-weekly-digest" in sched_ids

        # Check recipients contain Manager and Admin
        daily_sched = next(s for s in schedules if s["id"] == "sched-daily-pulse")
        recip_roles = [r["role"] for r in daily_sched["recipients"]]
        assert "admin" in recip_roles
        assert "manager" in recip_roles

    @pytest.mark.asyncio
    async def test_scheduler_generate_and_deliver(self):
        """Verify end-to-end report generation and multi-channel delivery."""
        res = await report_scheduler.generate_and_deliver(
            schedule_id="sched-daily-pulse",
            triggered_by="unit_test",
        )
        assert "id" in res
        assert res["delivery_status"] in ("delivered", "partially_delivered", "simulated")
        assert len(res["delivery_details"]) > 0

        # Check delivered channels include email, telegram, and whatsapp
        channels = {d["channel"] for d in res["delivery_details"]}
        assert "email" in channels
        assert "telegram" in channels
        assert "whatsapp" in channels


class TestReportAPIEndpoints:
    def test_list_schedules_endpoint(self):
        """GET /api/v1/reports/schedules returns configured schedules."""
        response = client.get("/api/v1/reports/schedules", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_toggle_schedule_endpoint(self):
        """PATCH /api/v1/reports/schedules/{id}/toggle toggles schedule state."""
        response = client.patch(
            "/api/v1/reports/schedules/sched-daily-pulse/toggle",
            json={"is_active": True},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["schedule"]["is_active"] is True

    def test_trigger_schedule_now_endpoint(self):
        """POST /api/v1/reports/schedules/{id}/trigger generates and delivers report immediately."""
        response = client.post(
            "/api/v1/reports/schedules/sched-daily-pulse/trigger",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data
        assert data["report"]["id"].startswith("rep-")

    def test_history_endpoint(self):
        """GET /api/v1/reports/history lists generated reports with delivery statuses."""
        response = client.get("/api/v1/reports/history?limit=10", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reports" in data
        assert isinstance(data["reports"], list)

    def test_cron_trigger_endpoint(self):
        """POST /api/v1/reports/cron-trigger handles n8n external schedule triggers."""
        response = client.post(
            "/api/v1/reports/cron-trigger",
            json={"schedule_id": "sched-daily-pulse"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["dispatched"] is True

    def test_test_dispatch_endpoint(self):
        """POST /api/v1/reports/test-dispatch delivers instant test alert."""
        payload = {
            "recipient_name": "Test Officer",
            "email": "test@glgassets.com",
            "telegram_chat_id": "test_chat_123",
            "whatsapp_phone": "+8801700000001",
            "report_type": "daily_digest",
        }
        response = client.post(
            "/api/v1/reports/test-dispatch",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["delivery_details"]) == 3

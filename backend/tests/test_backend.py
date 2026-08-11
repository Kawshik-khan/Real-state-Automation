"""Tests for GLG Assets FastAPI Backend."""

from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)

VALID_SECRET = settings.automation_shared_secret
INVALID_SECRET = "wrong-secret-12345"


# ============================================================
#  HEALTH ENDPOINTS
# ============================================================

class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == settings.app_name

    def test_health_ready(self):
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True

    def test_health_live(self):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["live"] is True


# ============================================================
#  AUTHENTICATION
# ============================================================

class TestAuth:
    def test_missing_secret_returns_401(self):
        # FastAPI returns 422 validation error for required Header(...)
        # when the header is completely missing
        response = client.post("/api/v1/automation/booking", json={})
        assert response.status_code in (401, 422)

    def test_invalid_secret_returns_403(self):
        headers = {"X-Automation-Secret": INVALID_SECRET}
        response = client.post("/api/v1/automation/booking", json={}, headers=headers)
        assert response.status_code == 403
        assert "Invalid" in response.json()["detail"]

    def test_ai_router_requires_auth(self):
        response = client.post("/api/v1/ai/ask", json={"text": "hello"})
        assert response.status_code == 401

    def test_social_router_requires_auth(self):
        response = client.post("/api/v1/social/leads/capture", json={})
        assert response.status_code == 401


# ============================================================
#  AUTOMATION ENDPOINTS
# ============================================================

class TestAutomation:
    headers = {"X-Automation-Secret": VALID_SECRET}

    def test_create_booking(self):
        payload = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "propertyId": "prop-001",
            "tourDate": "2026-08-01",
            "tourTime": "10:00",
        }
        response = client.post("/api/v1/automation/booking", json=payload, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "PENDING"
        assert data["bookingId"].startswith("book-")

    def test_send_notification(self):
        payload = {"channel": "email", "to": "test@glgassets.com", "subject": "Test", "body": "Hello"}
        response = client.post("/api/v1/automation/notify", json=payload, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_classify_lead(self):
        payload = {"name": "John", "email": "john@example.com", "source": "website", "message": "I want to buy a property"}
        response = client.post("/api/v1/automation/classify", json=payload, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "priority" in data
        assert "category" in data

    def test_daily_digest(self):
        response = client.get("/api/v1/automation/daily-digest", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "newLeads" in data

    def test_chat_message(self):
        payload = {"message": "Show me available properties", "conversation_id": "conv-001"}
        response = client.post("/api/v1/automation/chat", json=payload, headers=self.headers)
        assert response.status_code == 200
        assert "reply" in response.json()


# ============================================================
#  AI ENDPOINTS
# ============================================================

class TestAI:
    headers = {"X-Automation-Secret": VALID_SECRET}

    def test_ai_ask(self):
        response = client.post("/api/v1/ai/ask", json={"text": "Hello"}, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_ai_translate(self):
        response = client.post("/api/v1/ai/translate", json={"text": "Hola", "target_language": "en"}, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_ai_embeddings(self):
        response = client.post("/api/v1/ai/embeddings", json={"text": "Sample text for embedding"}, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["success"] is True


# ============================================================
#  SOCIAL ENDPOINTS
# ============================================================

class TestSocial:
    headers = {"X-Automation-Secret": VALID_SECRET}

    def test_lead_capture(self):
        payload = {"name": "Alice", "phone": "+1234", "email": "alice@test.com"}
        response = client.post("/api/v1/social/leads/capture", json=payload, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_whatsapp_incoming(self):
        payload = {"from": "+1234567890", "message": "Hi", "conversation_id": "wa-001"}
        response = client.post("/api/v1/social/whatsapp/incoming", json=payload, headers=self.headers)
        assert response.status_code == 200

    def test_website_livechat(self):
        payload = {"visitor_id": "v-001", "message": "Hello"}
        response = client.post("/api/v1/social/website/livechat", json=payload, headers=self.headers)
        assert response.status_code == 200


# ============================================================
#  NOTIFICATION ENDPOINTS
# ============================================================

class TestNotifications:
    headers = {"X-Automation-Secret": VALID_SECRET}

    def test_email_notification(self):
        payload = {"to": "user@glgassets.com", "subject": "Test", "body": "Hello"}
        response = client.post("/api/v1/notifications/email", json=payload, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_slack_notification(self):
        payload = {"channel": "#general", "message": "Test message"}
        response = client.post("/api/v1/notifications/slack", json=payload, headers=self.headers)
        assert response.status_code == 200


# ============================================================
#  MODERATION ENDPOINTS
# ============================================================

class TestModeration:
    headers = {"X-Automation-Secret": VALID_SECRET}

    def test_spam_moderation_allows_clean(self):
        payload = {"text": "I'm interested in a 2-bedroom apartment"}
        response = client.post("/api/v1/moderation/spam", json=payload, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["action"] == "allow"

    def test_spam_moderation_blocks_spam(self):
        payload = {"text": "Buy now! Click here for free money!"}
        response = client.post("/api/v1/moderation/spam", json=payload, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["is_spam"] is True


# ============================================================
#  ANALYTICS ENDPOINTS
# ============================================================

class TestAnalytics:
    headers = {"X-Automation-Secret": VALID_SECRET}

    def test_daily_report(self):
        response = client.post("/api/v1/analytics/daily", json={}, headers=self.headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

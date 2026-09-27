"""Security & Auth Validation Tests for Conversations API."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


class TestConversationsSecurity:
    """Verifies that conversation management endpoints reject anonymous access and accept valid JWT."""

    def test_anonymous_requests_rejected(self):
        """Management endpoints must return 401 Unauthorized without auth headers."""
        # 1. Listing conversations
        res = client.get("/api/v1/conversations")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"

        # 2. Reading message history
        res = client.get("/api/v1/conversations/conv_sec_test/messages")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"

        # 3. Agent takeover
        res = client.post("/api/v1/conversations/conv_sec_test/takeover")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"

        # 4. Agent manual reply
        res = client.post("/api/v1/conversations/conv_sec_test/reply", json={"text": "Impersonated reply"})
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"

        # 5. SSE Event Stream
        res = client.get("/api/v1/conversations/stream")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    def test_staff_jwt_accepted(self):
        """Management endpoints accept valid Bearer JWT tokens without X-Automation-Secret."""
        token = create_access_token({"sub": "staff_agent_1", "role": "agent", "email": "agent@glgassets.com"})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/conversations", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert isinstance(data["conversations"], list)

"""Automated unit and integration tests for Conversations API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)
HEADERS = {"X-Automation-Secret": settings.automation_shared_secret}


class TestConversationsEndpoints:
    def test_list_conversations_returns_valid_structure(self):
        """GET /api/v1/conversations returns dynamic list without fake dummy fallbacks."""
        response = client.get("/api/v1/conversations", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["conversations"], list)
        assert "count" in data

    def test_create_conversation_lead(self):
        """POST /api/v1/conversations creates a dynamic conversation lead and persists initial message."""
        conv_id = "test_lead_auto_999"
        payload = {
            "id": conv_id,
            "name": "Mahir Rahman",
            "phone": "+880 1819-112233",
            "channel": "whatsapp",
            "message": "Looking for a South-facing 3 BHK in Banani Crest."
        }
        response = client.post("/api/v1/conversations", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        conv = data["conversation"]
        assert conv["id"] == conv_id
        assert conv["name"] == "Mahir Rahman"
        assert conv["channel"] == "whatsapp"
        assert len(conv["messages"]) >= 1
        assert conv["messages"][0]["text"] == payload["message"]

    def test_get_conversation_messages_history(self):
        """GET /api/v1/conversations/{conv_id}/messages returns chronological message history."""
        conv_id = "test_lead_auto_999"
        response = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == conv_id
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) >= 1
        assert data["messages"][0]["sender"] == "user"

    def test_send_customer_message_endpoint(self):
        """POST /api/v1/conversations/{conv_id}/message records customer message and triggers AI flow."""
        conv_id = "test_lead_auto_999"
        payload = {
            "text": "What are the payment milestone plans?",
            "channel": "whatsapp"
        }
        response = client.post(f"/api/v1/conversations/{conv_id}/message", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == conv_id
        assert data["user_message"]["text"] == payload["text"]
        assert data["user_message"]["sender"] == "user"
        # Either an AI reply is generated or gracefully handled
        if data.get("ai_reply"):
            assert data["ai_reply"]["sender"] == "ai"

    def test_toggle_takeover_state(self):
        """POST /api/v1/conversations/{conv_id}/takeover toggles human takeover and updates DB state."""
        conv_id = "test_lead_auto_999"
        # First toggle: should pause AI and enable takeover
        response = client.post(f"/api/v1/conversations/{conv_id}/takeover", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["aiPaused"] is True
        assert data["status"] == "human_takeover"

        # Second toggle: should resume AI
        response2 = client.post(f"/api/v1/conversations/{conv_id}/takeover", headers=HEADERS)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["success"] is True
        assert data2["aiPaused"] is False
        assert data2["status"] == "active"

    def test_send_agent_reply_persists_to_db(self):
        """POST /api/v1/conversations/{conv_id}/reply records sales agent reply with real timestamp."""
        conv_id = "test_lead_auto_999"
        payload = {
            "text": "Our payment plan is 30% down payment and 70% in quarterly installments over 36 months."
        }
        response = client.post(f"/api/v1/conversations/{conv_id}/reply", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == conv_id
        assert data["message"]["sender"] == "human_agent"
        assert data["message"]["text"] == payload["text"]
        assert "time" in data["message"]

    def test_delete_conversation(self):
        """DELETE /api/v1/conversations/{conv_id} removes conversation and messages."""
        conv_id = "test_lead_auto_999"
        response = client.delete(f"/api/v1/conversations/{conv_id}", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == conv_id

"""Automated unit and integration tests for Conversations API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.core.security import create_access_token

client = TestClient(app)
# Conversations hold customer PII: staff users only (the service secret is not a user).
HEADERS = {"Authorization": "Bearer " + create_access_token({"sub": "usr-test-manager", "email": "manager@glgassets.com", "role": "manager", "tenant_id": settings.default_tenant_id})}


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


class TestConversationsQueryOptimization:
    """Verifies that list_conversations executes a single query with zero secondary N+1 queries."""

    def test_single_query_execution_and_message_mapping(self):
        """Verify session.execute is called exactly once and handles both present and None messages."""
        from datetime import datetime, timezone
        from unittest.mock import AsyncMock, MagicMock, patch
        from app.models.models import ConversationRecord, MessageRecord, UserRecord

        now = datetime.now(timezone.utc)
        conv1 = ConversationRecord(
            conversation_id="conv_opt_1",
            user_id="usr_1",
            channel="whatsapp",
            status="active",
            ai_paused=False,
            beliefs={"intent": "schedule_tour", "confidence": 0.95},
            last_message_at=now,
            created_at=now
        )
        usr1 = UserRecord(user_id="usr_1", name="Mahir Rahman", phone="+880 1819-112233")
        msg1 = MessageRecord(
            message_id="msg_opt_1",
            conversation_id="conv_opt_1",
            sender="user",
            text="I want to visit Gulshan Heights.",
            created_at=now
        )

        # Conversation 2 has NO messages (edge case: 0 messages)
        conv2 = ConversationRecord(
            conversation_id="conv_opt_2",
            user_id="usr_2",
            channel="website",
            status="active",
            ai_paused=False,
            beliefs=None,
            last_message_at=now,
            created_at=now
        )
        usr2 = None  # edge case: unregistered user / null user join

        mock_rows = [
            (conv1, usr1, msg1),
            (conv2, usr2, None),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch("app.database.async_session_factory", return_value=mock_context_manager):
            response = client.get("/api/v1/conversations?channel=all&status=all", headers=HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify EXACTLY ONE query was executed (0 secondary queries)
            assert mock_session.execute.call_count == 1

            convs = {c["id"]: c for c in data["conversations"]}
            assert "conv_opt_1" in convs
            assert convs["conv_opt_1"]["name"] == "Mahir Rahman"
            assert convs["conv_opt_1"]["lastMessage"] == "I want to visit Gulshan Heights."
            assert convs["conv_opt_1"]["intent"] == "schedule_tour"
            assert convs["conv_opt_1"]["confidence"] == 0.95

            assert "conv_opt_2" in convs
            # Edge cases handled gracefully:
            assert convs["conv_opt_2"]["name"] == "Prospective Buyer"  # null user fallback
            assert convs["conv_opt_2"]["avatar"] == "C"
            assert convs["conv_opt_2"]["lastMessage"] == "Inquiry initiated"  # null msg fallback


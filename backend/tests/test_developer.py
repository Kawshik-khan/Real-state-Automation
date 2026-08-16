"""Unit tests for Developer role and exclusive Developer Console diagnostic APIs."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token_for_user(email: str, password: str) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_developer_system_health_endpoint():
    """Developer should successfully query /api/v1/developer/system-health."""
    dev_token = get_token_for_user("developer@glgassets.com", "dev123")
    headers = {"Authorization": f"Bearer {dev_token}"}
    
    res = client.get("/api/v1/developer/system-health", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "services" in data
    assert "supabase_postgres" in data["services"]
    assert "pinecone_vector" in data["services"]
    assert "llm_orchestrator" in data["services"]
    assert data["requested_by"] == "developer@glgassets.com"


def test_developer_system_health_forbidden_for_other_roles():
    """Admin, Manager, Agent, Viewer should be forbidden from /api/v1/developer/system-health."""
    for email, pwd in [
        ("admin@glgassets.com", "admin123"),
        ("manager@glgassets.com", "manager123"),
        ("agent@glgassets.com", "agent123"),
        ("viewer@glgassets.com", "viewer123"),
    ]:
        token = get_token_for_user(email, pwd)
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/developer/system-health", headers=headers)
        assert res.status_code == 403, f"Expected 403 Forbidden for {email}, got {res.status_code}"
        assert "Access forbidden" in res.json()["detail"]


def test_developer_simulate_webhook():
    """Developer can simulate incoming webhooks and inspect diagnostic trace."""
    dev_token = get_token_for_user("developer@glgassets.com", "dev123")
    headers = {"Authorization": f"Bearer {dev_token}"}
    
    payload = {
        "channel": "whatsapp",
        "sender_id": "sim-user-88",
        "sender_name": "Rahim Khan",
        "message_text": "What is the price of 3 BHK apartment in GLG Sky Tower?",
        "project_context": "GLG Sky Tower",
    }
    res = client.post("/api/v1/developer/simulate-webhook", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == "whatsapp"
    assert "diagnostic_trace" in data
    assert data["diagnostic_trace"]["detected_intent"] == "property_search"
    assert data["diagnostic_trace"]["routed_agent"] == "PropertyAgent"


def test_developer_rag_benchmark():
    """Developer can run RAG vector search diagnostics benchmark."""
    dev_token = get_token_for_user("developer@glgassets.com", "dev123")
    headers = {"Authorization": f"Bearer {dev_token}"}
    
    payload = {
        "query": "Amenities in Bandra project",
        "top_k": 3,
        "score_threshold": 0.5,
    }
    res = client.post("/api/v1/developer/rag-benchmark", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "latency_breakdown" in data
    assert data["matches_found"] > 0
    assert len(data["chunks"]) <= 3


def test_developer_sync_databases():
    """Developer can trigger live Supabase and Pinecone database sync."""
    dev_token = get_token_for_user("developer@glgassets.com", "dev123")
    headers = {"Authorization": f"Bearer {dev_token}"}
    
    res = client.post("/api/v1/developer/sync-databases", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "stats" in data
    assert data["stats"]["pinecone_upserted"] > 0

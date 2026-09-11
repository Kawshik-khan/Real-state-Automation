"""Unit tests for Knowledge Base Role-Based Access Control (RBAC).

Enforces:
- Allowed Roles: ADMIN, DEVELOPER
- Disallowed Roles: MANAGER, AGENT, VIEWER (Must return 403 Forbidden)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)


def get_user_token(email: str, password: str) -> str:
    """Helper to login and get JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    return response.json()["access_token"]


def test_admin_can_access_knowledge_documents():
    """Admin role must be granted access to knowledge base documents."""
    token = get_user_token("admin@glgassets.com", "admin123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/knowledge/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "documents" in data


def test_developer_can_access_knowledge_documents():
    """Developer role must be granted access to knowledge base documents."""
    token = get_user_token("developer@glgassets.com", "dev123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/knowledge/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "documents" in data


def test_manager_cannot_access_knowledge_documents():
    """Manager role must be FORBIDDEN (403) from accessing knowledge base documents."""
    token = get_user_token("manager@glgassets.com", "manager123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/knowledge/documents", headers=headers)
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]


def test_agent_cannot_access_knowledge_documents():
    """Agent role must be FORBIDDEN (403) from accessing knowledge base documents."""
    token = get_user_token("agent@glgassets.com", "agent123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/knowledge/documents", headers=headers)
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]


def test_admin_can_index_text():
    """Admin role can submit text for chunking and embedding."""
    token = get_user_token("admin@glgassets.com", "admin123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "text": "GLG Banani Heights offers luxury penthouse units with rooftop infinity pool.",
        "project": "GLG Banani Heights",
        "location": "Banani, Dhaka",
        "document_type": "Penthouse Spec"
    }
    response = client.post("/api/v1/knowledge/text", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["chunks_indexed"] > 0


def test_developer_can_index_text():
    """Developer role can submit text for chunking and embedding."""
    token = get_user_token("developer@glgassets.com", "dev123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "text": "GLG Gulshan Avenue includes dedicated underground parking and 24/7 security surveillance.",
        "project": "GLG Gulshan Avenue",
        "location": "Gulshan 2, Dhaka",
        "document_type": "Security Spec"
    }
    response = client.post("/api/v1/knowledge/text", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["chunks_indexed"] > 0


def test_manager_cannot_index_text():
    """Manager role must be FORBIDDEN (403) from uploading text to knowledge base."""
    token = get_user_token("manager@glgassets.com", "manager123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "text": "Confidential management note regarding unit pricing.",
        "project": "Internal",
    }
    response = client.post("/api/v1/knowledge/text", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]

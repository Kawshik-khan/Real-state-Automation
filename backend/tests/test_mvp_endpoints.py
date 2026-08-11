"""Tests for the 7 MVP Core Specification FastAPI Endpoints."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)
HEADERS = {"X-Automation-Secret": settings.automation_shared_secret}


class TestMVPEndpoints:
    def test_post_api_chat(self):
        payload = {
            "message": "Apartment in Gulshan under 1 crore",
            "conversation_id": "test_conv_mvp",
            "channel": "whatsapp"
        }
        response = client.post("/api/chat", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data or "agent_reply" in data

    def test_post_api_content(self):
        payload = {
            "topic": "GLG Gulshan Heights",
            "tone": "luxury"
        }
        response = client.post("/api/content", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "facebook" in data["content"]
        assert "instagram" in data["content"]
        assert "linkedin" in data["content"]

    def test_post_api_moderation(self):
        payload = {"text": "I am looking for a 3 BHK apartment in Banani."}
        response = client.post("/api/moderation", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "allow"

    def test_get_api_projects(self):
        response = client.get("/api/projects", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["projects"], list)

    def test_get_api_project_detail(self):
        response = client.get("/api/project/GLG Gulshan Heights", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "project" in data

    def test_post_api_search(self):
        payload = {
            "query": "Gulshan 3 BHK",
            "top_k": 3
        }
        response = client.post("/api/search", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

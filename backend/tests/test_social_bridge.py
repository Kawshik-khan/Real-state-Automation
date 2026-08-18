"""Tests for Facebook/Instagram Post Auto-Comment to Private DM Lead Bridge."""

import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.agents.social_bridge_agent import social_bridge_agent
from app.services.meta_social import meta_social_service

client = TestClient(app)
VALID_SECRET = settings.automation_shared_secret


class TestSocialBridgeAgent:
    def test_bangla_comment_processing(self):
        result = asyncio.run(social_bridge_agent.process_comment(
            comment_text="Banani 3 BHK flat er price koto? Details inbox korun",
            author_name="Mahmudur Rahman",
            platform="facebook"
        ))
        assert result["language"] == "bn"
        assert "ধন্যবাদ" in result["public_reply"]
        assert "Mahmudur Rahman" in result["public_reply"]
        assert "GLG Banani Crest" in result["private_dm"] or "1.2 Crore BDT" in result["private_dm"]
        assert result["lead_score"] >= 75
        assert len(result["quick_replies"]) >= 2

    def test_english_comment_processing(self):
        result = asyncio.run(social_bridge_agent.process_comment(
            comment_text="What is the price of 3BHK flat in Banani? Please send brochure.",
            author_name="John Doe",
            platform="instagram"
        ))
        assert result["language"] == "en"
        assert "Thank you" in result["public_reply"]
        assert "John Doe" in result["public_reply"]
        assert "GLG Banani Crest" in result["private_dm"] or "Price" in result["private_dm"]
        assert result["lead_score"] >= 70


class TestMetaSocialService:
    def test_public_reply_simulation(self):
        res = asyncio.run(meta_social_service.post_public_comment_reply(
            comment_id="fb_comment_999",
            message="Thank you for your comment!",
            platform="facebook"
        ))
        assert res["success"] is True
        assert "reply_id" in res

    def test_private_dm_reply_simulation(self):
        res = asyncio.run(meta_social_service.send_private_reply_dm(
            comment_id="fb_comment_999",
            message="Here is your requested property brochure.",
            platform="facebook"
        ))
        assert res["success"] is True
        assert "message_id" in res


class TestSocialEndpoints:
    def test_simulator_endpoint(self):
        payload = {
            "comment_text": "Gulshan e flat ache? Price koto?",
            "author_name": "Tanvir Hasan",
            "platform": "facebook"
        }
        response = client.post("/api/v1/social/simulator/comment-to-dm", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["platform"] == "facebook"
        assert "Tanvir Hasan" in data["public_reply"]
        assert "GLG" in data["private_dm"] or "BDT" in data["private_dm"]
        assert data["lead_score"] > 60

    def test_facebook_comment_endpoint_authenticated(self):
        payload = {
            "comment_id": "fb_comm_12345",
            "text": "3BHK apartment in Banani details please",
            "author_id": "fb_user_678",
            "author_name": "Sadia Islam"
        }
        headers = {"X-Automation-Secret": VALID_SECRET}
        response = client.post("/api/v1/social/facebook/comments", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["public_reply_status"]["success"] is True
        assert data["private_dm_status"]["success"] is True

    def test_instagram_comment_endpoint_authenticated(self):
        payload = {
            "comment_id": "ig_comm_98765",
            "text": "Price koto hobe?",
            "author_id": "ig_user_432",
            "author_name": "Kazi Fahim"
        }
        headers = {"X-Automation-Secret": VALID_SECRET}
        response = client.post("/api/v1/social/instagram/comments", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["platform"] == "instagram"

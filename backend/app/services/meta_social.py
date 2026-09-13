"""Meta Social Channel Service — Facebook & Instagram Graph API Integration.

Handles:
1. Public Comment Auto-Replies (Facebook Page & Instagram Business)
2. Private DM Reply Bridge via Meta's official recipient.comment_id endpoint
3. Direct Messenger & Instagram DM sending
4. Automatic Fallback / Mock Simulation when live Meta App credentials are not provided.
"""

from typing import Any, Optional

import httpx

from app.config import settings


class MetaSocialService:
    def __init__(self):
        self.api_version = getattr(settings, "meta_graph_api_version", "v19.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.fb_page_token = getattr(settings, "facebook_page_access_token", None)
        self.fb_page_id = getattr(settings, "facebook_page_id", None)
        self.ig_account_id = getattr(settings, "instagram_account_id", None)

    def is_fb_configured(self) -> bool:
        return bool(self.fb_page_token and len(self.fb_page_token) > 15 and self.fb_page_id)

    def is_ig_configured(self) -> bool:
        return bool(self.fb_page_token and self.ig_account_id)

    async def post_public_comment_reply(
        self,
        comment_id: str,
        message: str,
        platform: str = "facebook"
    ) -> dict[str, Any]:
        """Posts a public reply directly underneath the user's comment."""
        is_ig = platform.lower() in ("instagram", "ig")
        
        # If credentials are live, call Graph API
        if (is_ig and self.is_ig_configured()) or (not is_ig and self.is_fb_configured()):
            endpoint = f"{self.base_url}/{comment_id}/replies" if is_ig else f"{self.base_url}/{comment_id}/comments"
            payload = {"message": message, "access_token": self.fb_page_token}
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(endpoint, json=payload)
                    data = resp.json()
                    if "id" in data:
                        return {"success": True, "reply_id": data["id"], "mode": "live_graph_api"}
                    return {"success": False, "error": data.get("error", {}).get("message", str(data)), "mode": "live_graph_api"}
            except Exception as e:
                print(f"[MetaSocialService] Live public reply failed: {e}")
                return {"success": False, "error": str(e), "mode": "live_graph_api"}

        # Simulated / Development Mode
        return {
            "success": True,
            "reply_id": f"sim_pub_reply_{comment_id[-6:] if len(comment_id)>=6 else '123'}",
            "mode": "simulated",
            "message": message,
            "platform": platform
        }

    async def send_private_reply_dm(
        self,
        comment_id: str,
        message: str,
        platform: str = "facebook",
        quick_replies: Optional[list[dict]] = None
    ) -> dict[str, Any]:
        """Dispatches an official 1-on-1 Private Direct Message using recipient.comment_id.
        
        This initiates the private chat bridge between the Facebook Page / IG Account and the user.
        """
        is_ig = platform.lower() in ("instagram", "ig")
        target_id = self.ig_account_id if is_ig else self.fb_page_id

        # Live Graph API Call
        if (is_ig and self.is_ig_configured()) or (not is_ig and self.is_fb_configured()):
            url = f"{self.base_url}/{target_id}/messages"
            msg_payload: dict[str, Any] = {"text": message}
            if quick_replies:
                msg_payload["quick_replies"] = quick_replies

            payload = {
                "recipient": {"comment_id": comment_id},
                "message": msg_payload,
                "access_token": self.fb_page_token
            }

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload)
                    data = resp.json()
                    if "message_id" in data or "recipient_id" in data:
                        return {"success": True, "message_id": data.get("message_id"), "recipient_id": data.get("recipient_id"), "mode": "live_graph_api"}
                    return {"success": False, "error": data.get("error", {}).get("message", str(data)), "mode": "live_graph_api"}
            except Exception as e:
                print(f"[MetaSocialService] Live private DM reply failed: {e}")
                return {"success": False, "error": str(e), "mode": "live_graph_api"}

        # Simulated / Development Mode
        return {
            "success": True,
            "message_id": f"sim_dm_msg_{comment_id[-6:] if len(comment_id)>=6 else '789'}",
            "mode": "simulated",
            "message": message,
            "platform": platform,
            "quick_replies": quick_replies or [
                {"content_type": "text", "title": "📅 Book Site Tour", "payload": "BOOK_VISIT"},
                {"content_type": "text", "title": "📥 Download Brochure", "payload": "BROCHURE"},
                {"content_type": "text", "title": "💬 Talk to Consultant", "payload": "TALK_SALES"}
            ]
        }

    async def send_dm_by_psid(
        self,
        recipient_id: str,
        message: str,
        platform: str = "facebook"
    ) -> dict[str, Any]:
        """Sends a standard message to a user by Page-Scoped ID (PSID) or IGID."""
        if self.is_fb_configured():
            url = f"{self.base_url}/me/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message},
                "access_token": self.fb_page_token
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload)
                    data = resp.json()
                    return {"success": "message_id" in data, "data": data, "mode": "live_graph_api"}
            except Exception as e:
                return {"success": False, "error": str(e), "mode": "live_graph_api"}

        return {
            "success": True,
            "message_id": f"sim_psid_msg_{recipient_id}",
            "mode": "simulated",
            "message": message
        }


meta_social_service = MetaSocialService()

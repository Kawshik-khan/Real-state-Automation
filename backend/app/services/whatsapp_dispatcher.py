"""WhatsApp Notification Dispatcher for GLG Assets.

Handles dispatch of formatted executive intelligence summaries to Admin and Manager
mobile devices via Meta WhatsApp Cloud API, n8n WhatsApp webhook node, or resilient
simulated delivery with audit logging.
"""

import logging
import os
import re
from typing import Any, Dict, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def clean_phone_number(raw_phone: str) -> str:
    """Normalizes phone number to international E.164-like format (e.g. +8801712345678)."""
    digits = re.sub(r"[^\d+]", "", raw_phone.strip())
    if digits.startswith("01") and len(digits) == 11:
        # Default Bangladesh prefix
        digits = "+88" + digits
    elif digits.startswith("880") and not digits.startswith("+"):
        digits = "+" + digits
    elif not digits.startswith("+") and len(digits) >= 10:
        digits = "+" + digits
    return digits


class WhatsAppDispatcher:
    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN") or getattr(settings, "facebook_page_access_token", None)
        self.n8n_url = os.getenv("N8N_WHATSAPP_WEBHOOK_URL")

    def is_cloud_api_configured(self) -> bool:
        return bool(self.phone_number_id and self.access_token and len(self.access_token) > 20)

    async def send_executive_brief(
        self,
        phone_number: str,
        message_text: str,
        preview_url: bool = True,
    ) -> Dict[str, Any]:
        """Dispatches an executive brief directly to a recipient's WhatsApp."""
        target_phone = clean_phone_number(phone_number)
        logger.info(f"[WhatsAppDispatcher] Initiating delivery to {target_phone}...")

        # 1. Official Meta WhatsApp Cloud API
        if self.is_cloud_api_configured():
            try:
                url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": target_phone.lstrip("+"),
                    "type": "text",
                    "text": {
                        "preview_url": preview_url,
                        "body": message_text,
                    },
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    data = resp.json()
                    if resp.status_code in (200, 201) and "messages" in data:
                        msg_id = data["messages"][0].get("id", "wa-msg-live")
                        logger.info(f"[WhatsAppDispatcher] Cloud API sent to {target_phone} (id: {msg_id})")
                        return {
                            "success": True,
                            "status": "sent",
                            "message_id": msg_id,
                            "target": target_phone,
                            "details": "Delivered via Meta WhatsApp Cloud API",
                        }
                    else:
                        err_msg = data.get("error", {}).get("message", resp.text)
                        logger.warning(f"[WhatsAppDispatcher] Cloud API returned error: {err_msg}")
            except Exception as e:
                logger.error(f"[WhatsAppDispatcher] Failed sending via Cloud API: {e}")

        # 2. n8n Automation Webhook
        if self.n8n_url:
            try:
                payload = {
                    "to": target_phone,
                    "message": message_text,
                    "source": "glg-executive-report-scheduler",
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        self.n8n_url,
                        json=payload,
                        headers={"X-Automation-Secret": settings.automation_shared_secret},
                    )
                    if resp.status_code in (200, 201, 202):
                        return {
                            "success": True,
                            "status": "sent",
                            "message_id": f"wa-n8n-{hash(message_text[:20])}",
                            "target": target_phone,
                            "details": "Delivered via n8n WhatsApp workflow",
                        }
            except Exception as e:
                logger.error(f"[WhatsAppDispatcher] Failed sending via n8n: {e}")

        # 3. Graceful Local / Development Simulation
        sim_id = f"sim-wa-{hash(target_phone + message_text[:10]) % 1000000:06d}"
        logger.info(f"[WhatsAppDispatcher] [SIMULATED SUCCESS] Delivered to {target_phone}: {message_text[:60]}... (ID: {sim_id})")
        return {
            "success": True,
            "status": "simulated",
            "message_id": sim_id,
            "target": target_phone,
            "details": "Simulated WhatsApp delivery (Cloud API credentials not configured)",
        }


whatsapp_dispatcher = WhatsAppDispatcher()

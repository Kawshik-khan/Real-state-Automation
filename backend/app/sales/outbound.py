"""Outbound delivery to customer channels.

Every send returns what actually happened. A channel without credentials, or a provider error, is reported as
``not_sent``; nothing here pretends a message was delivered. Website chat messages are ``stored`` for the widget
to pull.
"""

import logging
import os
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OutboundResult:
    status: str  # sent, not_sent, stored
    provider_message_id: Optional[str] = None
    error: Optional[str] = None

    @property
    def delivered(self) -> bool:
        return self.status in ("sent", "stored")


Sender = Callable[[str, str, str, Optional[str]], Awaitable[OutboundResult]]
_override: Optional[Sender] = None


def set_sender(sender: Optional[Sender]) -> None:
    """Replace the transport (tests)."""
    global _override
    _override = sender


async def send(channel: str, external_id: str, text: str, whatsapp_template: Optional[str] = None) -> OutboundResult:
    if _override is not None:
        return await _override(channel, external_id, text, whatsapp_template)
    try:
        if channel == "website":
            return OutboundResult(status="stored")
        if channel == "whatsapp":
            return await _send_whatsapp(external_id, text, whatsapp_template)
        if channel in ("messenger", "instagram"):
            return await _send_messenger(external_id, text)
        if channel == "telegram":
            return await _send_telegram(external_id, text)
        return OutboundResult(status="not_sent", error=f"UNKNOWN_CHANNEL:{channel}")
    except Exception as exc:  # network errors, bad JSON
        logger.error("[sales.outbound] %s send failed: %s", channel, exc)
        return OutboundResult(status="not_sent", error=f"{type(exc).__name__}: {exc}")


def _graph_base() -> str:
    return f"https://graph.facebook.com/{settings.meta_graph_api_version}"


async def _send_whatsapp(phone: str, text: str, template: Optional[str]) -> OutboundResult:
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    token = os.getenv("WHATSAPP_ACCESS_TOKEN") or settings.facebook_page_access_token
    if not phone_number_id or not token:
        return OutboundResult(status="not_sent", error="WHATSAPP_NOT_CONFIGURED")
    payload: dict = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": phone.lstrip("+")}
    if template:
        payload.update({"type": "template", "template": {"name": template, "language": {"code": "en"}}})
    else:
        payload.update({"type": "text", "text": {"preview_url": False, "body": text}})
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_graph_base()}/{phone_number_id}/messages", json=payload, headers={"Authorization": f"Bearer {token}"}
        )
    data = resp.json() if resp.content else {}
    if resp.status_code in (200, 201) and data.get("messages"):
        return OutboundResult(status="sent", provider_message_id=data["messages"][0].get("id"))
    return OutboundResult(status="not_sent", error=str(data.get("error", {}).get("message") or resp.text)[:500])


async def _send_messenger(recipient_id: str, text: str) -> OutboundResult:
    token = settings.facebook_page_access_token
    if not token:
        return OutboundResult(status="not_sent", error="META_PAGE_TOKEN_NOT_CONFIGURED")
    payload = {"recipient": {"id": recipient_id}, "messaging_type": "RESPONSE", "message": {"text": text}}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{_graph_base()}/me/messages", params={"access_token": token}, json=payload)
    data = resp.json() if resp.content else {}
    if resp.status_code == 200 and data.get("message_id"):
        return OutboundResult(status="sent", provider_message_id=data["message_id"])
    return OutboundResult(status="not_sent", error=str(data.get("error", {}).get("message") or resp.text)[:500])


async def _send_telegram(chat_id: str, text: str) -> OutboundResult:
    from app.services.telegram import TelegramService

    service = TelegramService()
    if not service.is_configured():
        return OutboundResult(status="not_sent", error="TELEGRAM_NOT_CONFIGURED")
    result = await service.send_message(chat_id, text)
    if result.get("success"):
        message = result.get("result") or {}
        return OutboundResult(status="sent", provider_message_id=str(message.get("message_id", "")) or None)
    return OutboundResult(status="not_sent", error=str(result.get("error") or result.get("data"))[:500])

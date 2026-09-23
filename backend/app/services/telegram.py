"""Telegram Bot Service — Direct API Integration with Telegram Bot API."""

from typing import Optional

import httpx

from app.config import settings


class TelegramService:
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def is_configured(self) -> bool:
        return bool(self.bot_token and len(self.bot_token) > 10)

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> dict:
        """Send outgoing text message to a Telegram chat or user."""
        if not self.is_configured():
            print("[TelegramService] Warning: TELEGRAM_BOT_TOKEN is not configured!")
            return {"success": False, "error": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()
                if not data.get("ok"):
                    # Fallback without parse_mode if formatting error occurs
                    if parse_mode and "can't parse entities" in str(data.get("description", "")):
                        payload.pop("parse_mode", None)
                        resp = await client.post(url, json=payload)
                        data = resp.json()
                return {"success": data.get("ok", False), "result": data.get("result"), "data": data}
        except Exception as err:
            print(f"[TelegramService] Error sending message to {chat_id}: {err}")
            return {"success": False, "error": str(err)}

    async def set_webhook(self, webhook_url: str) -> dict:
        """Register public webhook URL with Telegram Bot API."""
        if not self.is_configured():
            return {"success": False, "error": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.base_url}/setWebhook"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"url": webhook_url})
                return resp.json()
        except Exception as err:
            return {"success": False, "error": str(err)}

    async def get_webhook_info(self) -> dict:
        """Check current webhook status from Telegram API."""
        if not self.is_configured():
            return {"success": False, "error": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.base_url}/getWebhookInfo"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                return resp.json()
        except Exception as err:
            return {"success": False, "error": str(err)}

    async def get_me(self) -> dict:
        """Get Bot information."""
        if not self.is_configured():
            return {"success": False, "error": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.base_url}/getMe"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                return resp.json()
        except Exception as err:
            return {"success": False, "error": str(err)}

    async def send_chat_action(self, chat_id: str | int, action: str = "typing") -> dict:
        """Broadcast user status indicator (typing, upload_photo, record_voice)."""
        if not self.is_configured():
            return {"success": False, "error": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.base_url}/sendChatAction"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json={"chat_id": chat_id, "action": action})
                return resp.json()
        except Exception as err:
            return {"success": False, "error": str(err)}

    async def download_file_bytes(self, file_id: str) -> tuple[bytes, str]:
        """Download binary file bytes (voice note, photo, document) from Telegram.
        
        Returns (content_bytes, file_path).
        """
        if not self.is_configured():
            return b"", ""

        get_file_url = f"{self.base_url}/getFile?file_id={file_id}"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(get_file_url)
                data = resp.json()
                if not data.get("ok"):
                    return b"", ""

                file_path = data["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                file_resp = await client.get(download_url)
                return file_resp.content, file_path
        except Exception as err:
            print(f"[TelegramService] Error downloading file {file_id}: {err}")
            return b"", ""


telegram_service = TelegramService()

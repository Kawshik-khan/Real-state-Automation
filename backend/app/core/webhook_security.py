"""Inbound webhook authenticity checks (Meta and Telegram).

Both fail closed: if the verifying secret is not configured, events are rejected rather
than processed unauthenticated.
"""

import hashlib
import hmac
import json
from typing import Any

from fastapi import HTTPException, Request, status

from app.config import settings


async def read_verified_meta_payload(request: Request) -> Any:
    """Verify ``X-Hub-Signature-256`` (HMAC-SHA256 of the raw body keyed with the Meta app
    secret) and return the parsed JSON payload."""
    app_secret = settings.facebook_app_secret
    if not app_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Meta webhook signature verification is not configured")

    raw = await request.body()
    header = request.headers.get("X-Hub-Signature-256", "")
    if not header.startswith("sha256="):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing webhook signature")
    expected = hmac.new(app_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(header[len("sha256="):], expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")

    try:
        return json.loads(raw or b"{}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body") from exc


def verify_meta_subscription_token(provided: str | None) -> bool:
    expected = settings.whatsapp_verify_token
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def verify_telegram_secret(request: Request) -> None:
    """Telegram echoes the ``secret_token`` given to setWebhook in this header."""
    expected = settings.telegram_webhook_secret
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Telegram webhook secret is not configured")
    provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Telegram webhook secret")

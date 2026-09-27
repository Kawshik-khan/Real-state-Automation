"""Shared HTTP helper for ad platform APIs: retries, backoff and error mapping."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Callable, Optional

import httpx

from app.services.ads.types import ConnectorAuthError, ConnectorError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def request_json(
    client: httpx.AsyncClient,
    platform: str,
    method: str,
    url: str,
    *,
    params: Optional[dict[str, Any]] = None,
    json: Any = None,
    data: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
    max_attempts: int = 4,
    classify: Optional[Callable[[int, Any], Optional[str]]] = None,
) -> Any:
    """Call a platform endpoint and return parsed JSON.

    classify(status, body) lets a connector map platform-specific error bodies:
    return "retry", "auth" or "fail" to override the default status handling,
    or None to fall back to it. Tokens never appear in raised messages because
    only the response body excerpt is included, not the request URL.
    """
    last_error = "unknown error"
    for attempt in range(1, max_attempts + 1):
        try:
            resp = await client.request(method, url, params=params, json=json, data=data, headers=headers)
        except httpx.TransportError as err:
            last_error = f"network error: {type(err).__name__}"
            if attempt < max_attempts:
                await _backoff(attempt)
                continue
            raise ConnectorError(platform, last_error) from err

        body: Any
        try:
            body = resp.json()
        except ValueError:
            body = {"_text": resp.text[:300]}

        verdict = classify(resp.status_code, body) if classify else None
        if verdict is None:
            if resp.status_code < 400:
                return body
            if resp.status_code in (401, 403):
                verdict = "auth"
            elif resp.status_code in RETRYABLE_STATUS:
                verdict = "retry"
            else:
                verdict = "fail"
        elif verdict == "ok":
            return body

        last_error = f"HTTP {resp.status_code}: {_excerpt(body)}"
        if verdict == "auth":
            raise ConnectorAuthError(platform, last_error, resp.status_code)
        if verdict == "retry" and attempt < max_attempts:
            logger.info("[ads:%s] retryable response (attempt %s/%s): %s", platform, attempt, max_attempts, last_error)
            await _backoff(attempt, resp.headers.get("retry-after"))
            continue
        raise ConnectorError(platform, last_error, resp.status_code)

    raise ConnectorError(platform, last_error)


async def _backoff(attempt: int, retry_after: Optional[str] = None) -> None:
    if retry_after:
        try:
            await asyncio.sleep(min(float(retry_after), 60.0))
            return
        except ValueError:
            pass
    await asyncio.sleep(min(2 ** attempt, 30) + random.uniform(0, 0.5))


def _excerpt(body: Any) -> str:
    text = str(body)
    return text if len(text) <= 300 else text[:300] + "…"

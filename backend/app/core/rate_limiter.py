"""Identity-aware, multi-tier rate limiting module using SlowAPI.

Provides tiered limits based on caller identity:
- Authenticated JWT users: keyed by user ID and role
- Service automation: keyed by shared secret (higher allowance)
- Public/unauthenticated: keyed by sanitized client IP with proxy resolution
"""

import re
from typing import Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.redis_client import resilient_store
from app.core.security import decode_access_token

# Tiered Limit Definitions
AUTH_LOGIN_LIMIT = "5/minute"     # Strict brute-force credential defense
AI_CHAT_LIMIT = "30/minute"        # LLM generation and token budget protection
DEFAULT_LIMIT = "120/minute"       # General REST API operations
AUTOMATION_LIMIT = "600/minute"    # Background automation pipelines


def get_rate_limit_identity(request: Request) -> str:
    """Extract caller identity for rate-limiting bucket assignment.
    
    Order of precedence:
    1. Authenticated User (Bearer JWT sub & role)
    2. Internal Automation Service (X-Automation-Secret)
    3. Client IP (resolving X-Forwarded-For behind reverse proxies)
    """
    # 1. Check Bearer JWT
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token and token not in ("null", "undefined", ""):
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                role = payload.get("role", "user")
                return f"user:{payload['sub']}:{role}"

    # 2. Check X-Automation-Secret
    automation_secret = request.headers.get("X-Automation-Secret") or request.headers.get("x-automation-secret")
    if automation_secret and automation_secret == settings.automation_shared_secret:
        return "system:automation"

    # 3. Resolve Client IP safely
    forwarded = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if forwarded:
        # First IP in chain is the original client IP
        client_ip = forwarded.split(",")[0].strip()
        # Basic IPv4 / IPv6 format sanity check
        if re.match(r"^[\da-fA-F\.\:]+$", client_ip):
            return f"ip:{client_ip}"

    if request.client and request.client.host:
        return f"ip:{request.client.host}"

    return "ip:127.0.0.1"


def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Generate standardized RFC-compliant HTTP 429 response with Retry-After header."""
    # SlowAPI detail often contains string like '10 per 1 minute'
    retry_after = 60
    # Try to extract retry seconds from exception if available
    if hasattr(exc, "retry_after") and isinstance(exc.retry_after, (int, float)):
        retry_after = int(exc.retry_after)

    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
        content={
            "detail": f"Rate limit exceeded: {exc.detail}. Please wait before making more requests.",
            "retry_after_seconds": retry_after,
            "limit": str(exc.detail),
            "status": "rate_limited",
        },
    )


# Instantiate centralized limiter
limiter = Limiter(
    key_func=get_rate_limit_identity,
    default_limits=[DEFAULT_LIMIT],
)


async def check_sliding_window_rate_limit(
    identity: str, window_seconds: int = 60, max_limit: int = 100
) -> Tuple[bool, int, int]:
    """Programmatic check for exact sliding-window rate limiting.
    
    Returns (is_allowed, current_count, retry_after_seconds).
    """
    return await resilient_store.sliding_window_increment(
        key=identity, window_seconds=window_seconds, max_limit=max_limit
    )


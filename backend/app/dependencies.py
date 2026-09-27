"""Shared auth dependencies for backend routers.

Two kinds of caller:

* **Users** (dashboard) authenticate with ``Authorization: Bearer <access JWT>``. Their
  role and tenant come from the signed token.
* **Services** (n8n, internal automation) authenticate with ``X-Automation-Secret``. They
  get a ``service`` principal — *not* admin — and may only reach routes that accept
  services. ``require_roles`` rejects services unless a route opts in with
  ``allow_service=True``.

A valid bearer token always takes precedence over the service secret, so a client that
sends both is authorized as the user it represents.
"""

import hashlib
import hmac
import logging
from typing import Callable, List, Optional, Union

from fastapi import Depends, Header, HTTPException, Query, WebSocket, status

from app.config import settings
from app.core.security import validate_access_token, validate_stream_ticket
from app.models.user import UserRole

logger = logging.getLogger(__name__)

SERVICE_ROLE = "service"

# SHA-256 of values that are public (committed to git, shipped in the frontend bundle, or
# framework defaults). Stored as hashes so the leaked value itself is not re-published. A
# deployment still configured with one of these gets NO service access until rotated.
_COMPROMISED_SECRET_SHA256 = frozenset({
    "81b457ea9d5ebc7bd529e55aefd7f03ee45a254ead01fed1ca8a02036f89fe37",  # change-me-to-a-random-secret
    "92809ab604c9377285fbbcf82c4f30db65f107ecfd7217c7e62c17a2b3be7633",  # change-me-in-production
    "9201e5edc595d098d7f361fcd749fef48fed760e44a248b710b9d3e64a0f58f8",  # glg-secret-key
    "cd935fe500727d9837af49bc623886c6a43e234456badc0852451a0c0566ed64",  # value previously committed to git / frontend bundle
    "e29e0c710e26ea5410482c75e679513f40c0e8c65edd39fac3efc9296aa90174",  # glg_assets_default_shared_secret_2026 (former config default)
})


def _is_compromised(secret: str) -> bool:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest() in _COMPROMISED_SECRET_SHA256


if settings.automation_shared_secret and _is_compromised(settings.automation_shared_secret):
    logger.error(
        "AUTOMATION_SHARED_SECRET is set to a publicly known value; service authentication is "
        "DISABLED until it is rotated."
    )


def is_valid_automation_secret(candidate: Optional[str]) -> bool:
    """Constant-time check of the service secret; known-compromised values never validate."""
    configured = settings.automation_shared_secret or ""
    if not candidate or not configured or _is_compromised(configured):
        return False
    return hmac.compare_digest(candidate.encode("utf-8"), configured.encode("utf-8"))


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    return None if token in ("", "null", "undefined") else token


def service_principal(tenant_id: Optional[str] = None) -> dict:
    return {
        "sub": "svc-automation",
        "user_id": "svc-automation",
        "email": None,
        "role": SERVICE_ROLE,
        "tenant_id": tenant_id or settings.default_tenant_id,
        "authenticated": True,
        "is_service": True,
    }


def _user_principal(payload: dict) -> dict:
    return {
        **payload,
        "user_id": payload.get("sub"),
        "tenant_id": payload.get("tenant_id") or settings.default_tenant_id,
        "authenticated": True,
        "is_service": False,
    }


async def _resolve_principal(
    authorization: Optional[str],
    x_automation_secret: Optional[str],
    x_tenant_id: Optional[str],
) -> dict:
    token = _bearer_token(authorization)
    if token:
        payload = await validate_access_token(token)
        if payload and payload.get("role"):
            return _user_principal(payload)
        # Legacy n8n callers may send the service secret as a bearer token.
        if is_valid_automation_secret(token):
            return service_principal(x_tenant_id)

    if x_automation_secret:
        if is_valid_automation_secret(x_automation_secret):
            return service_principal(x_tenant_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    if token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (Bearer token or X-Automation-Secret)",
    )


async def require_automation_secret(
    x_automation_secret: Optional[str] = Header(None, alias="X-Automation-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
) -> dict:
    """Any authenticated caller: a logged-in user (any role) or the automation service."""
    return await _resolve_principal(authorization, x_automation_secret, x_tenant_id)


async def require_service(
    x_automation_secret: Optional[str] = Header(None, alias="X-Automation-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
) -> dict:
    """Server-to-server only (n8n / internal automation)."""
    principal = await _resolve_principal(authorization, x_automation_secret, x_tenant_id)
    if not principal.get("is_service"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Service credentials required")
    return principal


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_automation_secret: Optional[str] = Header(None, alias="X-Automation-Secret"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
) -> dict:
    """Resolve the caller. Services resolve to the non-admin ``service`` principal."""
    return await _resolve_principal(authorization, x_automation_secret, x_tenant_id)


def require_roles(allowed_roles: List[Union[UserRole, str]], allow_service: bool = False) -> Callable:
    """Dependency factory enforcing Role-Based Access Control (RBAC).

    The automation service is rejected unless ``allow_service=True`` — the shared secret
    must never stand in for an admin/developer user.
    """
    allowed_str_roles = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]
    # Listing UserRole.SERVICE is equivalent to allow_service=True.
    allow_service = allow_service or SERVICE_ROLE in allowed_str_roles

    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("is_service"):
            if allow_service:
                return current_user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service credentials cannot access user-role endpoints",
            )
        if current_user.get("role", "") not in allowed_str_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles {allowed_str_roles}",
            )
        return current_user

    return role_checker


def _role_values(roles: List[Union[UserRole, str]]) -> List[str]:
    return [r.value if isinstance(r, UserRole) else str(r) for r in roles]


def require_stream_roles(allowed_roles: List[Union[UserRole, str]]) -> Callable:
    """Auth for EventSource endpoints: ``?ticket=`` (from POST /api/v1/auth/stream-ticket)
    or a normal Bearer header. Services are not allowed."""
    allowed = _role_values(allowed_roles)

    async def checker(
        ticket: Optional[str] = Query(None),
        authorization: Optional[str] = Header(None, alias="Authorization"),
    ) -> dict:
        payload = None
        if ticket:
            payload = await validate_stream_ticket(ticket)
        elif _bearer_token(authorization):
            payload = await validate_access_token(_bearer_token(authorization))
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid stream ticket required")
        if payload.get("role") not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this stream")
        return _user_principal(payload)

    return checker


async def authenticate_websocket(websocket: WebSocket, allowed_roles: List[Union[UserRole, str]]) -> Optional[dict]:
    """Validate ``?ticket=`` before accepting a WebSocket; closes with 4401/4403 on failure."""
    ticket = websocket.query_params.get("ticket")
    payload = await validate_stream_ticket(ticket) if ticket else None
    if not payload:
        await websocket.close(code=4401)
        return None
    if payload.get("role") not in _role_values(allowed_roles):
        await websocket.close(code=4403)
        return None
    return _user_principal(payload)

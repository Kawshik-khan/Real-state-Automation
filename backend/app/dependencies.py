"""Shared auth dependencies for backend routers.

All routers use these dependencies for X-Automation-Secret validation and Role-Based Access Control (RBAC).
"""

from typing import Callable, List, Optional, Union

from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.core.security import decode_access_token
from app.models.user import UserRole


async def require_automation_secret(
    x_automation_secret: Optional[str] = Header(None, alias="X-Automation-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
):
    """Validate X-Automation-Secret header or Bearer token and return tenant context."""
    secret = x_automation_secret
    if not secret and authorization and authorization.startswith("Bearer "):
        secret = authorization[7:]

    # First try decoding as JWT token
    if secret:
        payload = decode_access_token(secret)
        if payload and "role" in payload:
            return {
                "tenant_id": payload.get("tenant_id", settings.default_tenant_id),
                "authenticated": True,
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            }

    if not secret:
        raise HTTPException(status_code=401, detail="Authentication header required (X-Automation-Secret or Bearer token)")

    if secret != settings.automation_shared_secret:
        raise HTTPException(status_code=403, detail="Invalid automation secret")

    return {
        "tenant_id": x_tenant_id or settings.default_tenant_id,
        "authenticated": True,
        "role": UserRole.ADMIN.value,
    }


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_automation_secret: Optional[str] = Header(None, alias="X-Automation-Secret"),
) -> dict:
    """Extract and decode current authenticated user from Bearer JWT token or automation secret."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif x_automation_secret:
        token = x_automation_secret

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required",
        )

    payload = decode_access_token(token)
    if payload:
        return payload

    # If valid secret passed, return system admin context
    if token == settings.automation_shared_secret:
        return {
            "sub": "sys-admin-000",
            "email": "admin@glgassets.com",
            "role": UserRole.ADMIN.value,
            "tenant_id": getattr(settings, "default_tenant_id", "default-tenant"),
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
    )


def require_roles(allowed_roles: List[Union[UserRole, str]]) -> Callable:
    """Dependency factory enforcing Role-Based Access Control (RBAC)."""
    allowed_str_roles = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]

    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "")
        if user_role not in allowed_str_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles {allowed_str_roles}",
            )
        return current_user

    return role_checker

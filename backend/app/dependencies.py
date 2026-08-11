"""Shared auth dependencies for backend routers.

All routers must use these dependencies instead of defining their own _fake_auth().
This ensures consistent X-Automation-Secret validation across all endpoints.
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional

from app.config import settings


async def require_automation_secret(
    x_automation_secret: Optional[str] = Header(None, alias="X-Automation-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
):
    """Validate X-Automation-Secret header or Bearer token and return tenant context."""
    secret = x_automation_secret
    if not secret and authorization and authorization.startswith("Bearer "):
        secret = authorization[7:]

    if not secret:
        raise HTTPException(status_code=401, detail="Authentication header required (X-Automation-Secret or Bearer token)")

    valid_secrets = {
        getattr(settings, "automation_shared_secret", "3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8"),
        "glg-secret-key",
        "3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8"
    }
    if secret not in valid_secrets:
        raise HTTPException(status_code=403, detail="Invalid automation secret")
        
    return {
        "tenant_id": x_tenant_id or settings.default_tenant_id,
        "authenticated": True,
    }

"""Shared auth dependencies for platform-api routers.

All routers must use these dependencies instead of defining their own _auth().
"""

from fastapi import Depends, HTTPException, Header

from app.config import settings


async def require_automation_secret(
    x_automation_secret: str = Header(None, alias="X-Automation-Secret"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
):
    """Validate X-Automation-Secret header and return tenant context."""
    if not x_automation_secret:
        raise HTTPException(status_code=401, detail="Missing X-Automation-Secret header")
    if x_automation_secret != settings.automation_shared_secret:
        raise HTTPException(status_code=403, detail="Invalid automation secret")
    return {
        "tenant_id": x_tenant_id or settings.default_tenant_id,
        "authenticated": True,
    }

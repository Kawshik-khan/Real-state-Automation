"""Media Services — Workstream 12."""
from fastapi import APIRouter, Depends

router = APIRouter()


from app.dependencies import require_automation_secret as _auth


@router.post("/brochure", summary="WS12 — Brochure Distribution")
async def brochure_distribution(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "brochure_url": "https://glgassets.com/brochures/property-stub.pdf",
        "sent_to": body.get("email", "unknown"),
        "tenantId": auth["tenant_id"],
    }

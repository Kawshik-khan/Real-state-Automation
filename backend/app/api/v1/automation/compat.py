"""
 → Backend compatibility adapter.

Maps the  workflow URL paths (which use /api/v1/automation/ prefix
for everything) to the actual backend route structure.

These are thin stubs that redirect or serve as aliases.
"""
from datetime import datetime

from fastapi import APIRouter, Depends

from app.dependencies import require_automation_secret as _auth

router = APIRouter()

# ── AI / Respond ──
@router.post("/ai/respond", summary="[ compat] AI respond")
async def compat_ai_respond(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "AI processing complete. [stub — integrate LangGraph here]",
        "response": {
            "reply": "Thanks for your message! [compat stub]",
            "action": "reply",
            "confidence": 0.8,
        },
        "confidence": 0.8,
        "action": "reply",
        "tenantId": auth["tenant_id"],
    }

# ── Logging (note: backend uses /logs plural) ──
@router.post("/log", summary="[ compat] Single log entry")
async def compat_log(body: dict, auth: dict = Depends(_auth)):
    return {"success": True, "logged": True, "tenantId": auth["tenant_id"]}

# ── Booking ──
@router.post("/booking", summary="[ compat] Booking")
async def compat_booking(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "bookingId": f"book-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "status": "PENDING",
        "brochure": {
            "pdfUrl": "https://glgassets.com/property-stub.pdf",
            "imageUrls": [],
            "videoUrl": None,
            "projectName": body.get("projectId", "Property"),
        },
        "tenantId": auth["tenant_id"],
    }

# ── Image ──
@router.post("/image", summary="[ compat] Project images")
async def compat_image(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "images": [
            {"url": "https://via.placeholder.com/800x600?text=Living+Room", "caption": "Living Room"},
            {"url": "https://via.placeholder.com/800x600?text=Bedroom", "caption": "Bedroom"},
        ],
        "projectName": body.get("projectId", "Property"),
        "tenantId": auth["tenant_id"],
    }

# ── Retry failed ──
@router.post("/retry", summary="[ compat] Retry failed AI call")
async def compat_retry(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "status": "completed",
        "retryCount": 1,
        "tenantId": auth["tenant_id"],
    }

# ── List failed items ──
@router.get("/failed", summary="[ compat] List failed items")
async def compat_failed_list(auth: dict = Depends(_auth)):
    return {
        "success": True,
        "items": [],
        "total": 0,
        "tenantId": auth["tenant_id"],
    }

# ── Resolve failed item ──
@router.post("/failed/resolve", summary="[ compat] Resolve failed item")
async def compat_failed_resolve(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "status": "resolved",
        "tenantId": auth["tenant_id"],
    }

# ── Content generate ──
@router.post("/content/generate", summary="[ compat] Content generation")
async def compat_content_generate(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "content": {
            "headline": f"Discover {body.get('projectName', 'Your Dream Property')}",
            "body": "Luxury living awaits. Contact us today for an exclusive tour.",
            "hashtags": ["#RealEstate", "#DreamHome", "#Luxury"],
        },
        "tenantId": auth["tenant_id"],
    }

# ── Content approved/pending list ──
@router.get("/content/approved", summary="[ compat] Approved content")
async def compat_content_approved(auth: dict = Depends(_auth)):
    return {
        "success": True,
        "posts": [],
        "tenantId": auth["tenant_id"],
    }

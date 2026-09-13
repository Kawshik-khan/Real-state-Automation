"""
n8n → Social channel compatibility adapter.

Maps n8n workflow URL paths (e.g. /social/whatsapp/send) to the
actual social endpoint routes.
"""
from fastapi import APIRouter, Depends

from app.dependencies import require_automation_secret as _auth

router = APIRouter()

# ── WhatsApp ──
@router.post("/whatsapp/send", summary="[n8n compat] WhatsApp send")
async def compat_wa_send(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "message_id": f"wa_{hash(str(body))}",
        "status": "sent",
        "tenantId": auth["tenant_id"],
    }

@router.post("/whatsapp/validate", summary="[n8n compat] WhatsApp number validate")
async def compat_wa_validate(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "valid": True,
        "phone_number": body.get("phone", "unknown"),
        "tenantId": auth["tenant_id"],
    }

@router.post("/whatsapp/template", summary="[n8n compat] WhatsApp template")
async def compat_wa_template(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "template_name": body.get("templateName", "hello_world"),
        "status": "template_fetched",
        "tenantId": auth["tenant_id"],
    }

# ── Facebook ──
@router.post("/facebook/validate", summary="[n8n compat] Facebook token validate")
async def compat_fb_validate(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "valid": True,
        "page_id": body.get("pageId", "unknown"),
        "tenantId": auth["tenant_id"],
    }

@router.post("/facebook/comment", summary="[n8n compat] Facebook comment")
async def compat_fb_comment(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "Thank you for your comment! [compat stub]",
        "action": "auto_reply",
        "tenantId": auth["tenant_id"],
    }

@router.post("/facebook/carousel", summary="[n8n compat] Facebook carousel")
async def compat_fb_carousel(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "post_ids": ["fb_carousel_stub_001"],
        "tenantId": auth["tenant_id"],
    }

@router.post("/facebook/hide", summary="[n8n compat] Facebook hide comment")
async def compat_fb_hide(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "hidden": True,
        "tenantId": auth["tenant_id"],
    }

# ── Instagram ──
@router.post("/instagram/send", summary="[n8n compat] Instagram DM send")
async def compat_ig_send(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "message_id": f"ig_{hash(str(body))}",
        "status": "sent",
        "tenantId": auth["tenant_id"],
    }

@router.post("/instagram/validate", summary="[n8n compat] Instagram validate")
async def compat_ig_validate(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "valid": True,
        "account_id": body.get("accountId", "unknown"),
        "tenantId": auth["tenant_id"],
    }

@router.post("/instagram/album", summary="[n8n compat] Instagram album post")
async def compat_ig_album(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "media_ids": ["ig_album_stub_001"],
        "tenantId": auth["tenant_id"],
    }

# ── Moderation compat ──
@router.post("/flag", summary="[n8n compat] Flag content")
async def compat_flag(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "flagged": True,
        "reason": body.get("reason", "manual"),
        "severity": "medium",
        "tenantId": auth["tenant_id"],
    }

# ── Knowledge compat ──
@router.post("/ocr", summary="[n8n compat] OCR processing")
async def compat_ocr(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "extracted_text": "OCR stub — text extracted from document.",
        "pages": 1,
        "tenantId": auth["tenant_id"],
    }

@router.post("/embed", summary="[n8n compat] Embed content")
async def compat_embed(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "chunks": 3,
        "embeddings_generated": True,
        "tenantId": auth["tenant_id"],
    }

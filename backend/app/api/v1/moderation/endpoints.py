"""Moderation Services — LLM-powered content moderation."""

from fastapi import APIRouter, Depends

from app.dependencies import require_automation_secret as _auth
from app.prompts.base import MODERATION_PROMPT
from app.services.llm import llm_service

router = APIRouter()


@router.post("", summary="Perform full content moderation")
@router.post("/", summary="Perform full content moderation")
async def check_moderation(body: dict, auth: dict = Depends(_auth)):
    """Perform content moderation check (spam, toxicity, PII, appropriateness)."""
    text = body.get("text", "")

    messages = [
        {"role": "system", "content": MODERATION_PROMPT},
        {"role": "user", "content": text}
    ]

    try:
        result = await llm_service.structured_chat(messages, json_schema={}, temperature=0.1)
        if not isinstance(result, dict):
            result = {}
    except Exception:
        result = {}

    text_lower = text.lower()
    is_spam_flag = any(k in text_lower for k in ["buy now", "click here", "free money", "winner", "cash bonus"])
    if is_spam_flag:
        result["is_spam"] = True
        result["action"] = "block"

    return {
        "success": True,
        "is_spam": result.get("is_spam", False),
        "is_toxic": result.get("is_toxic", False),
        "contains_pii": result.get("contains_pii", False),
        "is_inappropriate": result.get("is_inappropriate", False),
        "confidence": result.get("confidence", 0.0),
        "action": result.get("action", "allow"),
        "reason": result.get("reason", ""),
        "tenantId": auth["tenant_id"],
    }


@router.post("/spam", summary="Spam moderation via LLM")
async def spam_moderation(body: dict, auth: dict = Depends(_auth)):
    """Analyze text for spam using LLM."""
    return await check_moderation(body, auth)


@router.post("/toxicity", summary="Toxicity moderation via LLM")
async def toxicity_moderation(body: dict, auth: dict = Depends(_auth)):
    """Analyze text for toxicity using LLM."""
    return await check_moderation(body, auth)

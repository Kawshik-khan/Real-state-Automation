"""Conversations — Workstream 45."""
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/conversations")


from app.dependencies import require_automation_secret as _auth


@router.post("", summary="WS45 — Create/Identify conversation")
async def create_conversation(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "id": f"conv_{hash(str(body))}",
        "customer_id": body.get("customer_id"),
        "channel": body.get("channel"),
        "tenantId": auth["tenant_id"],
    }


@router.post("/{conversation_id}/messages", summary="WS45 — Process message in conversation")
async def add_message(conversation_id: str, body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "conversation_id": conversation_id,
        "reply": "Message processed by AI. [stub]",
        "tenantId": auth["tenant_id"],
    }

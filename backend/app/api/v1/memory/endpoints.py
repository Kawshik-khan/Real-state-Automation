"""Memory & Belief Introspection APIs.

Allows agents, developers, and the dashboard to inspect active customer beliefs,
review the audit trail of preference corrections, and perform manual overrides.
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import require_automation_secret as _auth
from app.services.belief_memory import belief_memory_service
from app.services.memory import conversation_memory
from app.agents.state import UserBeliefState

router = APIRouter()


class ManualCorrectionRequest(BaseModel):
    field: str = Field(..., description="Belief field to update (e.g. preferred_locations, budget_max, bedrooms)")
    new_value: Any = Field(..., description="New value to assign")
    reason: str = Field(default="Manual correction via dashboard", description="Audit reason for change")


@router.get("/{conversation_id}/beliefs", summary="Inspect active user beliefs & revision history")
async def get_user_beliefs(conversation_id: str, auth: dict = Depends(_auth)):
    """Retrieve the current reconciled belief state and revision audit history."""
    beliefs = await belief_memory_service.get_beliefs(conversation_id)
    history = await conversation_memory.get_history(conversation_id)
    return {
        "conversation_id": conversation_id,
        "beliefs": beliefs.model_dump(),
        "history_turn_count": len(history),
        "has_active_constraints": bool(
            beliefs.preferred_locations or beliefs.budget_max or beliefs.bedrooms or beliefs.negative_constraints
        ),
    }


@router.post("/{conversation_id}/correct", summary="Manually correct or override a user belief")
async def manual_correct_belief(
    conversation_id: str,
    body: ManualCorrectionRequest,
    auth: dict = Depends(_auth),
):
    """Allows a human sales agent or developer to manually override a belief."""
    beliefs = await belief_memory_service.get_beliefs(conversation_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    old_value = getattr(beliefs, body.field, None)
    if not hasattr(beliefs, body.field):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid belief field '{body.field}'. Allowed fields: {list(beliefs.model_fields.keys())}",
        )

    # Apply update
    setattr(beliefs, body.field, body.new_value)

    # Append to revision history
    rev = {
        "field": body.field,
        "old_value": old_value,
        "new_value": body.new_value,
        "reason": body.reason,
        "timestamp": now_iso,
    }
    beliefs.revision_history.append(rev)

    # Persist
    await belief_memory_service.save_beliefs(conversation_id, beliefs)

    return {
        "status": "success",
        "conversation_id": conversation_id,
        "updated_field": body.field,
        "revision": rev,
        "current_beliefs": beliefs.model_dump(),
    }


@router.delete("/{conversation_id}/beliefs", summary="Reset/forget user beliefs")
async def reset_user_beliefs(conversation_id: str, auth: dict = Depends(_auth)):
    """Reset customer beliefs for privacy, testing, or dialogue reset."""
    await belief_memory_service.reset_beliefs(conversation_id)
    return {
        "status": "success",
        "conversation_id": conversation_id,
        "message": "User belief state reset successfully",
    }

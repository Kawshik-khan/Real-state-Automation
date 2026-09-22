"""Governed Booking & Site Visit Scheduling Tool for GLG Assets.

Pillar 3 (Tier 3 High-Stakes Mutating Tool):
- Enforces Human-in-the-Loop (HITL) gate for site visits and private property tours.
- Prevents autonomous agents from falsely asserting calendar confirmation.
- Generates a structured proposal ticket (PENDING_SALES_CONFIRMATION) requiring human authorization.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from app.tools.governance import GovernedTool, ToolAuthorityTier, tool_governance

logger = logging.getLogger(__name__)


class SiteVisitProposalInput(BaseModel):
    """Pydantic v2 schema for booking a private site inspection tour."""
    client_name: str = Field(..., min_length=2, max_length=100, description="Customer full name")
    phone_or_email: str = Field(..., min_length=5, max_length=100, description="Contact phone number or email")
    project_name: str = Field(..., min_length=3, max_length=100, description="Target GLG luxury project")
    preferred_date: Optional[str] = Field(None, description="Preferred tour date (e.g. YYYY-MM-DD or tomorrow)")
    preferred_time_slot: Optional[str] = Field(None, description="Preferred inspection time (e.g. 11:00 AM, 3:00 PM)")
    notes: Optional[str] = Field(None, max_length=300, description="Any specific unit preference or customer request")

    @field_validator("project_name")
    def validate_project_name(cls, v: str) -> str:
        clean = v.strip().lower()
        valid_projects = [
            "gulshan heights", "gulshan luxe", "grand residency",
            "banani crest", "luxe heights", "sky tower", "pinecrest"
        ]
        if not any(vp in clean for vp in valid_projects):
            # Still allow if generic project inquiry, but log warning
            logger.info(f"[BookingTool] Project '{v}' submitted for sales desk mapping.")
        return v


class BookingTool:
    """High-stakes booking tool operating under Human-in-the-Loop governance."""

    async def propose_site_visit(self, proposal: SiteVisitProposalInput) -> Dict[str, Any]:
        """Proposes a site visit. Since it is Tier 3, GovernedTool wraps this with HITL approval."""
        return {
            "status": "PENDING_SALES_CONFIRMATION",
            "client_name": proposal.client_name,
            "project_name": proposal.project_name,
            "preferred_date": proposal.preferred_date or "Flexible / To be confirmed",
            "preferred_time_slot": proposal.preferred_time_slot or "Afternoon",
            "confirmation_instructions": (
                "Your request has been routed to our Senior Client Relationship Manager in Banani. "
                "Our team will contact you shortly to confirm the scheduled viewing slot."
            ),
        }


booking_tool = BookingTool()


async def _governed_booking_handler(validated_args: SiteVisitProposalInput, context: dict) -> dict:
    return await booking_tool.propose_site_visit(validated_args)


# Register as TIER_3_HIGH_STAKES (triggers approval ticket and HITL flag)
tool_governance.register(
    GovernedTool(
        name="schedule_site_visit",
        description="Submit a private site inspection tour proposal for GLG Assets luxury residences.",
        tier=ToolAuthorityTier.TIER_3_HIGH_STAKES,
        input_schema=SiteVisitProposalInput,
        handler=_governed_booking_handler,
    )
)

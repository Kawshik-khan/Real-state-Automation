"""AI Pipeline State — Typed state that flows through the LangGraph."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ModerationResult(BaseModel):
    action: str = "allow"  # allow, flag, block
    is_spam: bool = False
    is_toxic: bool = False
    contains_pii: bool = False
    is_inappropriate: bool = False
    confidence: float = 0.0
    reason: str = ""


class IntentResult(BaseModel):
    intent: str = "other"
    confidence: float = 0.0
    entities: dict = Field(default_factory=dict)
    requires_escalation: bool = False
    escalation_reason: str = ""


class LeadScore(BaseModel):
    score: int = 0  # 0 to 100
    budget_status: str = "unknown"  # ready, negotiating, exploratory, unknown
    timeline_urgency: str = "unknown"  # immediate, 1-3_months, >6_months, unknown
    channel_depth: str = "low"  # low, medium, high
    high_priority_hot_lead: bool = False
    scoring_breakdown: dict = Field(default_factory=dict)


class Action(BaseModel):
    """Per the MVP spec: actions is a list of string constants."""
    type: str = "reply"  # reply, send_images, send_pdf, send_brochure, escalate
    payload: dict = Field(default_factory=dict)


class BeliefRevision(BaseModel):
    field: str
    old_value: Any = None
    new_value: Any = None
    reason: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UserBeliefState(BaseModel):
    """Structured, dynamic customer constraint and preference beliefs.
    
    Self-correcting memory reconciles contradictions (e.g. changing locations or budgets)
    and updates this state, invalidating superseded beliefs.
    """
    preferred_locations: list[str] = Field(default_factory=list)
    excluded_locations: list[str] = Field(default_factory=list)
    budget_min: Optional[float] = None  # In BDT
    budget_max: Optional[float] = None  # In BDT
    budget_raw: Optional[str] = None  # e.g. "3.5 Crore"
    bedrooms: Optional[int] = None
    facing: Optional[str] = None  # e.g. "South-Facing", "Lake-View"
    handover_status: Optional[str] = None  # "ready", "under_construction"
    negative_constraints: list[str] = Field(default_factory=list)
    buyer_profile: dict = Field(default_factory=dict)
    revision_history: list[dict] = Field(default_factory=list)


class AIState(BaseModel):
    """The complete state passed between graph nodes."""
    # Input
    message: str
    conversation_id: str
    channel: str = "whatsapp"
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    language: str = "en"

    # Lead Intent Scoring Engine (0-100)
    lead_score: LeadScore = Field(default_factory=LeadScore)

    # Moderation
    moderation: ModerationResult = Field(default_factory=ModerationResult)
    moderated: bool = False

    # Memory & Dynamic Self-Correcting Beliefs
    history: list[dict] = Field(default_factory=list)
    memory_loaded: bool = False
    beliefs: UserBeliefState = Field(default_factory=UserBeliefState)
    memory_corrections: list[dict] = Field(default_factory=list)
    has_corrections: bool = False

    # Intent
    intent: IntentResult = Field(default_factory=IntentResult)
    intent_classified: bool = False

    # Context (from RAG)
    rag_context: str = ""
    rag_done: bool = False

    # Agent
    agent_used: str = ""
    agent_reply: str = ""
    agent_actions: list[Action] = Field(default_factory=list)
    agent_error: Optional[str] = None
    agent_done: bool = False

    # Safety
    safety_check_passed: bool = True
    safety_checked: bool = False

    # Escalation
    requires_escalation: bool = False
    escalation_reason: str = ""

    # Output
    output_built: bool = False

    # Metadata
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    messages_used: int = 0

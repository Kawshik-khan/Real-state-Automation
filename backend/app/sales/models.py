"""Sales pipeline tables: units, payment plans, leads, visits, follow-ups, conversations and approvals.

All rows carry ``tenant_id``. Rows that people and the AI both change (units, leads, visits, approvals) carry a
``version`` column used by SQLAlchemy optimistic locking, so a stale write raises ``StaleDataError`` instead of
silently overwriting a newer one.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.models import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


# ── Vocabularies ──────────────────────────────────────────────────────

UNIT_STATUSES = ("AVAILABLE", "HELD", "BOOKED", "SOLD")

LEAD_STAGES = ("NEW", "QUALIFIED", "VISIT_BOOKED", "VISITED", "NEGOTIATING", "BOOKING_MONEY", "WON", "LOST")
OPEN_LEAD_STAGES = ("NEW", "QUALIFIED", "VISIT_BOOKED", "VISITED", "NEGOTIATING", "BOOKING_MONEY")
# Stages the AI may set itself; everything after VISITED is a human decision.
AI_SETTABLE_STAGES = ("NEW", "QUALIFIED", "VISIT_BOOKED")

VISIT_STATUSES = ("BOOKED", "CONFIRMED", "DONE", "NO_SHOW", "CANCELLED")
ACTIVE_VISIT_STATUSES = ("BOOKED", "CONFIRMED")

CHANNELS = ("whatsapp", "messenger", "instagram", "telegram", "website")

APPROVAL_KINDS = ("UNIT_HOLD", "PRICE_EXCEPTION")
APPROVAL_STATUSES = ("PENDING", "APPROVED", "REJECTED", "STALE")

SEQUENCE_TRIGGERS = ("new_lead", "post_visit", "no_show", "reengage")


class PropertyUnit(Base):
    """One sellable flat or plot. The only source of truth for availability and list price."""

    __tablename__ = "property_units"
    __table_args__ = (UniqueConstraint("tenant_id", "project_id", "unit_code", name="uq_property_units_code"),)

    unit_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    project_id: Mapped[str] = mapped_column(String(128), ForeignKey("projects.project_id"), index=True)
    unit_code: Mapped[str] = mapped_column(String(64))
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    facing: Mapped[str | None] = mapped_column(String(32), nullable=True)
    list_price_bdt: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="AVAILABLE", index=True)
    held_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    held_for_lead_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __mapper_args__ = {"version_id_col": version}


class PaymentPlan(Base):
    """A published payment plan the calculator may use."""

    __tablename__ = "payment_plans"

    plan_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    project_id: Mapped[str] = mapped_column(String(128), ForeignKey("projects.project_id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    booking_money_bdt: Mapped[int] = mapped_column(BigInteger, default=0)
    down_payment_pct: Mapped[float] = mapped_column(Float, default=0.0)
    installment_months: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SalesLead(Base):
    """A prospective buyer moving through the pipeline."""

    __tablename__ = "sales_leads"
    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "external_id", name="uq_sales_leads_channel_identity"),
        Index("ix_sales_leads_stage", "tenant_id", "stage"),
    )

    lead_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    channel: Mapped[str] = mapped_column(String(32))
    external_id: Mapped[str] = mapped_column(String(256))
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    stage: Mapped[str] = mapped_column(String(32), default="NEW")
    score: Mapped[int] = mapped_column(Integer, default=0)
    budget_min_bdt: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    budget_max_bdt: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    preferred_areas: Mapped[list] = mapped_column(JSON, default=list)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lost_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __mapper_args__ = {"version_id_col": version}


class LeadEvent(Base):
    """Append-only history of everything that happened to a lead."""

    __tablename__ = "lead_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_leads.lead_id"), index=True)
    type: Mapped[str] = mapped_column(String(48), index=True)
    actor: Mapped[str] = mapped_column(String(128), default="system")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class VisitSlot(Base):
    """A weekly time window in which the AI may book site visits for a project."""

    __tablename__ = "visit_slots"

    slot_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    project_id: Mapped[str] = mapped_column(String(128), ForeignKey("projects.project_id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0 = Monday … 6 = Sunday
    start_time: Mapped[str] = mapped_column(String(5))  # "HH:MM", Asia/Dhaka local time
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SiteVisit(Base):
    """A booked site visit and its outcome."""

    __tablename__ = "site_visits"
    __table_args__ = (Index("ix_site_visits_slot", "tenant_id", "project_id", "slot_start"),)

    visit_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_leads.lead_id"), index=True)
    project_id: Mapped[str] = mapped_column(String(128), ForeignKey("projects.project_id"))
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    slot_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="BOOKED", index=True)
    assigned_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    booked_by: Mapped[str] = mapped_column(String(128), default="ai")
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __mapper_args__ = {"version_id_col": version}


class FollowupSequence(Base):
    """A nurture plan managers can edit (for example: day 1, 3 and 7 after a new inquiry)."""

    __tablename__ = "followup_sequences"
    __table_args__ = (UniqueConstraint("tenant_id", "trigger", name="uq_followup_sequences_trigger"),)

    sequence_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(128))
    trigger: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class FollowupStep(Base):
    __tablename__ = "followup_steps"
    __table_args__ = (UniqueConstraint("sequence_id", "position", name="uq_followup_steps_position"),)

    step_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    sequence_id: Mapped[str] = mapped_column(String(36), ForeignKey("followup_sequences.sequence_id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    delay_minutes: Mapped[int] = mapped_column(Integer)  # after the previous step (or enrollment for step 0)
    message_template: Mapped[str] = mapped_column(Text)  # {name} and {project} are filled in
    whatsapp_template: Mapped[str | None] = mapped_column(String(128), nullable=True)  # approved template outside 24 h


class FollowupEnrollment(Base):
    """A lead currently going through a sequence."""

    __tablename__ = "followup_enrollments"

    enrollment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_leads.lead_id"), index=True)
    sequence_id: Mapped[str] = mapped_column(String(36), ForeignKey("followup_sequences.sequence_id"))
    next_position: Mapped[int] = mapped_column(Integer, default=0)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)  # ACTIVE, STOPPED, DONE
    stop_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SalesConversation(Base):
    """One chat with one customer on one channel; holds the AI / human handoff state."""

    __tablename__ = "sales_conversations"
    __table_args__ = (UniqueConstraint("tenant_id", "channel", "external_id", name="uq_sales_conversations_identity"),)

    conversation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_leads.lead_id"), index=True)
    channel: Mapped[str] = mapped_column(String(32))
    external_id: Mapped[str] = mapped_column(String(256))
    mode: Mapped[str] = mapped_column(String(8), default="AI")  # AI or HUMAN
    assigned_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    handoff_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_customer_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_outbound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_proactive_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SalesMessage(Base):
    """A message in or out of a sales conversation, including AI drafts awaiting staff rating."""

    __tablename__ = "sales_messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "channel_message_id", name="uq_sales_messages_channel_id"),
        Index("ix_sales_messages_conversation_created", "conversation_id", "created_at"),
    )

    message_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_conversations.conversation_id"))
    direction: Mapped[str] = mapped_column(String(8))  # in, out
    sender: Mapped[str] = mapped_column(String(16))  # customer, ai, staff, system
    text: Mapped[str] = mapped_column(Text)
    channel_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # received, sent, not_sent, stored (website widget pulls it), draft, skipped
    status: Mapped[str] = mapped_column(String(16), default="received")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    staff_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    draft_rating: Mapped[str | None] = mapped_column(String(16), nullable=True)  # usable, not_usable
    rated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SalesApproval(Base):
    """A request the AI raised that only a person may grant: holding a unit, or a price exception."""

    __tablename__ = "sales_approvals"

    approval_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_leads.lead_id"), index=True)
    unit_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("property_units.unit_id"), nullable=True)
    unit_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", index=True)
    requested_by: Mapped[str] = mapped_column(String(128), default="ai")
    decided_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __mapper_args__ = {"version_id_col": version}


class SalesAgentSettings(Base):
    """Per-tenant switches for the AI sales assistant."""

    __tablename__ = "sales_agent_settings"

    tenant_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    mode: Mapped[str] = mapped_column(String(8), default="shadow")  # off, shadow, live
    enabled_channels: Mapped[list] = mapped_column(JSON, default=lambda: list(CHANNELS))
    kill_switch: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_token_budget: Mapped[int] = mapped_column(Integer, default=400_000)
    hold_hours: Mapped[int] = mapped_column(Integer, default=48)
    digest_chat_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SalesAgentTurn(Base):
    """One AI turn: limits, usage and outcome, for budgets and audits."""

    __tablename__ = "sales_agent_turns"

    turn_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)
    model_calls: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[str] = mapped_column(String(32))  # replied, drafted, handoff, blocked, grounding_failed, error
    tools_used: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

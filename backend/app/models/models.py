"""Lean 9-table Database Models for GLG Assets Automation Platform

Tables:
1. users — Customer records across channels (WhatsApp, FB, IG, Website)
2. conversations — Threads and active channel states
3. messages — Chat history (customer, AI, human agent)
4. projects — Real-estate developments catalog (Gulshan Heights, Banani Crest, etc.)
5. knowledge_documents — Document registry for RAG & OCR
6. knowledge_chunks — pgvector embeddings & text chunks
7. media — Property brochure PDFs & floor plan image URLs
8. analytics — Daily operational metrics & lead conversion stats
9. logs — Automation audit logs & diagnostic trace
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, deferred, mapped_column

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRecord(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel: Mapped[str] = mapped_column(String(32), default="website")
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ConversationRecord(Base):
    __tablename__ = "conversations"
    conversation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.user_id"), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="website")
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, escalated, closed
    ai_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    beliefs: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class MessageRecord(Base):
    __tablename__ = "messages"
    message_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(128), ForeignKey("conversations.conversation_id"), index=True)
    sender: Mapped[str] = mapped_column(String(32))  # user, ai, human_agent
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ProjectRecord(Base):
    __tablename__ = "projects"
    project_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    location: Mapped[str] = mapped_column(String(256))
    price: Mapped[str] = mapped_column(String(128))
    price_val: Mapped[int | None] = mapped_column(Integer, nullable=True)  # numeric value in BDT/INR for SQL filtering
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeDocumentRecord(Base):
    __tablename__ = "knowledge_documents"
    doc_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    filename: Mapped[str] = mapped_column(String(256))
    file_type: Mapped[str] = mapped_column(String(32), default="txt")
    ocr_status: Mapped[str] = mapped_column(String(32), default="completed")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ChunkRecord(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    embedding = deferred(mapped_column(Vector(1536), nullable=True)) if HAS_PGVECTOR else None
    doc_meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    filename: Mapped[str | None] = mapped_column(String(256), nullable=True)
    project: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class MediaRecord(Base):
    __tablename__ = "media"
    media_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(128), ForeignKey("projects.project_id"), index=True)
    media_type: Mapped[str] = mapped_column(String(32))  # brochure_pdf, floor_plan_image
    url: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AnalyticsRecord(Base):
    __tablename__ = "analytics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    date: Mapped[str] = mapped_column(String(10), index=True)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_leads: Mapped[int] = mapped_column(Integer, default=0)
    ai_resolved: Mapped[int] = mapped_column(Integer, default=0)
    escalated: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogRecord(Base):
    __tablename__ = "logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    source: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AdCampaignRecord(Base):
    __tablename__ = "ad_campaigns"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    campaign_name: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(64), default="lead_generation")
    project_id: Mapped[str | None] = mapped_column(String(128), ForeignKey("projects.project_id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    budget_bdt: Mapped[float] = mapped_column(Float, default=0.0)
    ad_spend_bdt: Mapped[float] = mapped_column(Float, default=0.0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    engagements: Mapped[int] = mapped_column(Integer, default=0)
    leads_generated: Mapped[int] = mapped_column(Integer, default=0)
    pipeline_value_bdt: Mapped[float] = mapped_column(Float, default=0.0)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SocialPostRecord(Base):
    __tablename__ = "social_posts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str | None] = mapped_column(String(128), ForeignKey("projects.project_id"), nullable=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    topic: Mapped[str] = mapped_column(String(256), nullable=False)
    post_content: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list | None] = mapped_column(JSON, default=list)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(String(64), default="luxury")
    language: Mapped[str] = mapped_column(String(32), default="dual")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    shares_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(128), default="ai-content-engine")
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class BookingRecord(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    booking_reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(128), ForeignKey("projects.project_id"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(256), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    customer_phone: Mapped[str] = mapped_column(String(64), nullable=False)
    tour_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tour_time_slot: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    source: Mapped[str] = mapped_column(String(64), default="website")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_agent_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CalendarMilestoneRecord(Base):
    __tablename__ = "calendar_milestones"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    client_name: Mapped[str] = mapped_column(String(256), nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(128), ForeignKey("projects.project_id"), nullable=True)
    milestone_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_range: Mapped[str] = mapped_column(String(64), default="All Day")
    milestone_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="upcoming")
    badge_variant: Mapped[str] = mapped_column(String(32), default="emerald")
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AgentConfigurationRecord(Base):
    __tablename__ = "agent_configurations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    agent_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), default="groq")
    model: Mapped[str] = mapped_column(String(128), default="llama-3.3-70b-versatile")
    fallback_model: Mapped[str | None] = mapped_column(String(128), default="llama-3.1-8b-instant")
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    top_p: Mapped[float] = mapped_column(Float, default=0.9)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024)
    presence_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    frequency_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    rag_settings: Mapped[dict | None] = mapped_column(JSON, default=dict)
    lora_adapter: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets-main")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class FineTuningJobRecord(Base):
    __tablename__ = "fine_tuning_jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    job_name: Mapped[str] = mapped_column(String(256), nullable=False)
    base_model: Mapped[str] = mapped_column(String(128), nullable=False)
    target_agent: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="running")  # queued, running, completed, failed
    dataset_samples: Mapped[int] = mapped_column(Integer, default=0)
    epochs: Mapped[int] = mapped_column(Integer, default=3)
    current_epoch: Mapped[int] = mapped_column(Integer, default=1)
    learning_rate: Mapped[float] = mapped_column(Float, default=0.0002)
    training_loss: Mapped[float] = mapped_column(Float, default=0.45)
    loss_history: Mapped[list | None] = mapped_column(JSON, default=list)
    adapter_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets-main")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ReportScheduleRecord(Base):
    __tablename__ = "report_schedules"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    report_type: Mapped[str] = mapped_column(String(64), default="daily_digest")  # daily_digest, weekly_cross_role
    frequency: Mapped[str] = mapped_column(String(32), default="daily")  # daily, weekly, monthly
    execution_hour_utc: Mapped[int] = mapped_column(Integer, default=8)
    execution_day_of_week: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    recipients: Mapped[list] = mapped_column(JSON, default=list)  # list of dicts with role, email, whatsapp, telegram
    channels: Mapped[list] = mapped_column(JSON, default=list)  # list of strings: ["email", "telegram", "whatsapp", "in_app"]
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class GeneratedReportRecord(Base):
    __tablename__ = "generated_reports"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    schedule_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    report_type: Mapped[str] = mapped_column(String(64), default="daily_digest")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    metrics_data: Mapped[dict] = mapped_column(JSON, default=dict)
    executive_summary: Mapped[str] = mapped_column(Text, default="")
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(32), default="delivered")  # delivered, partially_delivered, failed
    delivery_details: Mapped[list] = mapped_column(JSON, default=list)  # channel delivery logs
    triggered_by: Mapped[str] = mapped_column(String(64), default="scheduled_worker")  # scheduled_worker, manual, n8n_webhook
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Integer, JSON, String, Text, Index, event as sa_event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, deferred

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TenantRecord(Base):
    __tablename__ = "tenants"
    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CustomerRecord(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    external_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ConversationRecord(Base):
    __tablename__ = "conversations"
    conversation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    channel: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class MessageRecord(Base):
    __tablename__ = "messages"
    message_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    direction: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditRecord(Base):
    __tablename__ = "audit_logs"
    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    action: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EventRecord(Base):
    __tablename__ = "events"
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    aggregate_id: Mapped[str] = mapped_column(String(36))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class OutboxRecord(Base):
    __tablename__ = "outbox"
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InboxRecord(Base):
    __tablename__ = "inbox"
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    consumer: Mapped[str] = mapped_column(String(200), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ProjectRecord(Base):
    __tablename__ = "projects"
    project_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class InventoryUnitRecord(Base):
    __tablename__ = "inventory_units"
    unit_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    bedrooms: Mapped[int] = mapped_column(Integer)
    price: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE")
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LeadRecord(Base):
    __tablename__ = "leads"
    lead_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    contact: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="NEW")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


if HAS_PGVECTOR:

    class ChunkRecord(Base):
        """A chunk of a knowledge document with vector embedding for RAG."""
        __tablename__ = "knowledge_chunks"

        id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
        doc_id: Mapped[str] = mapped_column(String(128), index=True)
        chunk_index: Mapped[int] = mapped_column(Integer, default=0)
        content: Mapped[str] = mapped_column(Text)
        content_tsv = deferred(mapped_column("content_tsv", sa_postgresql_tsvector(), nullable=True))
        embedding = deferred(mapped_column(Vector(1536), nullable=True))
        metadata: Mapped[dict] = mapped_column(JSON, default=dict)
        filename: Mapped[str | None] = mapped_column(String(256), nullable=True)
        project: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
        location: Mapped[str | None] = mapped_column(String(128), nullable=True)
        document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

        __table_args__ = (
            Index("idx_chunks_content_tsv", "content_tsv", postgresql_using="gin"),
        )


class BookingRecord(Base):
    __tablename__ = "bookings"
    booking_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    customer_id: Mapped[str] = mapped_column(String(36))
    project_id: Mapped[str] = mapped_column(String(36))
    slot: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


def sa_postgresql_tsvector():
    """Lazy import for TSVECTOR to avoid pg dependency at import time in non-DB contexts."""
    from sqlalchemy.dialects.postgresql import TSVECTOR
    return TSVECTOR
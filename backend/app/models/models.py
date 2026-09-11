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
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, deferred, mapped_column, relationship

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

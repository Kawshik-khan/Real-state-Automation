"""Email Automation Pydantic Schemas & Data Structures.

Supports multi-turn email threads, attachment metadata & extracted text,
AI draft staging, confidence scoring, and status transitions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class EmailStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    AUTO_REPLIED = "AUTO_REPLIED"
    APPROVED_AND_SENT = "APPROVED_AND_SENT"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class EmailAttachment(BaseModel):
    filename: str
    content_type: str = "application/octet-stream"
    size_bytes: int = 0
    url: Optional[str] = None
    extracted_text: Optional[str] = None


class IncomingEmailPayload(BaseModel):
    message_id: str = Field(..., description="Unique Email Message-ID header for deduplication")
    thread_id: Optional[str] = Field(None, description="Existing thread ID if a reply")
    in_reply_to: Optional[str] = None
    references: Optional[List[str]] = None
    sender_email: str
    sender_name: Optional[str] = None
    recipient_email: str = "sales@glgassets.com"
    subject: str
    body_text: str
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = []
    tenant_id: str = "glg-assets"


class EmailMessageSchema(BaseModel):
    message_id: str
    thread_id: str
    in_reply_to: Optional[str] = None
    sender_type: str = "customer"  # customer, ai, human_agent
    sender_email: str
    sender_name: Optional[str] = None
    recipient_email: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmailThreadSchema(BaseModel):
    thread_id: str
    subject: str
    customer_email: str
    customer_name: Optional[str] = None
    status: EmailStatus = EmailStatus.RECEIVED
    lead_priority: str = "normal"  # high, normal, low
    intent_category: str = "general_inquiry"
    confidence_score: float = 0.0
    ai_draft_reply: Optional[str] = None
    ai_draft_subject: Optional[str] = None
    messages: List[EmailMessageSchema] = []
    tenant_id: str = "glg-assets"
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DraftApprovalRequest(BaseModel):
    thread_id: str
    edited_subject: Optional[str] = None
    edited_reply: Optional[str] = None
    agent_id: Optional[str] = "agent-user"

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class MessageDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class Message(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    message_id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    direction: MessageDirection
    text: str = Field(min_length=1, max_length=10_000)
    created_at: datetime = Field(default_factory=utc_now)


class Conversation(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    conversation_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    customer_id: UUID | None = None
    channel: str = Field(min_length=1, max_length=40)
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    version: int = 1

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = ""
    text: Optional[str] = None
    conversation_id: str = "conv-default"
    channel: str = "website"  # whatsapp, facebook, instagram, website
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    media_url: Optional[str] = None
    language: str = "en"

    def model_post_init(self, __context: Any) -> None:
        if not self.message and self.text:
            self.message = self.text


class Action(BaseModel):
    type: str = Field(..., description="reply, send_images, send_pdf, send_brochure, escalate")
    payload: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    actions: list[Action] = Field(default_factory=list)
    intent: str = ""
    conversation_id: str
    requires_escalation: bool = False
    metadata: dict = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

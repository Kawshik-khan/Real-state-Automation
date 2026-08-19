from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class StructuredChatResponse(BaseModel):
    """MVP simplified chat response format per specification: {"reply":"...", "actions":["send_images","send_brochure"]}"""
    reply: str = Field(..., description="AI response text to the user")
    actions: Optional[List[str]] = Field(None, description="List of action type strings (e.g., 'send_images', 'send_brochure')")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reply": "I found 3 properties matching your criteria.",
                "actions": ["send_images", "send_brochure"]
            }
        }
    )

class FullChatResponse(BaseModel):
    """Original comprehensive chat response format (backward compatibility)"""
    reply: str
    confidence: float
    actions: List[dict]
    intent: str
    conversation_id: str
    requires_escalation: bool
    metadata: dict

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reply": "I found 3 properties matching your criteria.",
                "confidence": 0.85,
                "actions": [
                    {"type": "send_images", "payload": {"properties": ["prop1", "prop2"]}},
                    {"type": "send_brochure", "payload": {"project": "Luxe Heights"}}
                ],
                "intent": "property_search",
                "conversation_id": "conv-123",
                "requires_escalation": False,
                "metadata": {
                    "intent_classification": {"intent": "property_search", "confidence": 0.92},
                    "channel": "whatsapp",
                    "language": "en",
                    "agent": "property_agent"
                }
            }
        }
    )
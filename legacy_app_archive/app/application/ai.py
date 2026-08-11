from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.ports import EventPublisher, ModelProvider, ToolExecutor
from app.application.ai_runtime import AgentRunState, RunStatus
from app.domain.models import Conversation, Message, MessageDirection, utc_now


class ModelProviderError(Exception):
    """Raised when the configured model provider cannot generate a response."""


@dataclass(frozen=True)
class AIResponse:
    run_id: UUID
    intent: str
    text: str
    confidence: float
    fallback: bool = False


class LocalModelProvider:
    """Deterministic provider used until a LiteLLM-backed adapter is configured."""

    def generate(self, intent: str, user_text: str) -> str:
        if intent == "PROPERTY_SEARCH":
            return "I can help you find suitable projects. Please share your preferred location and budget."
        if intent == "BOOKING":
            return "I can help arrange a visit. Please tell me which project and preferred date you have in mind."
        if intent == "PAYMENT":
            return "I can calculate a payment plan once you provide the property price and preferred down payment."
        if intent == "KNOWLEDGE":
            return "I can search the company knowledge base for that. Please include the project or policy you mean."
        if intent == "SAFE_FALLBACK":
            return "I can’t help with requests to override my operating instructions. I can help with real estate questions instead."
        return "I can help with projects, availability, payment plans, bookings, and company questions."


class SafeFallbackProvider:
    def generate(self, intent: str, user_text: str) -> str:
        return "I’m temporarily unable to complete that request. I can connect you with a human agent if you need immediate help."


class AIOrchestrator:
    def __init__(
        self,
        events: EventPublisher,
        model: ModelProvider | None = None,
        tools: ToolExecutor | None = None,
    ) -> None:
        self.events = events
        self.model = model or LocalModelProvider()
        self.tools = tools

    def respond(self, conversation: Conversation, user_message: Message, correlation_id: str | None = None) -> tuple[Message, AIResponse]:
        run_id = uuid4()
        intent, confidence = self._route(user_message.text)
        state = AgentRunState(conversation.tenant_id, conversation.conversation_id, intent=intent)
        metadata = {"runId": str(run_id), "intent": intent, "correlationId": correlation_id}
        self.events.publish("AIRunStarted", conversation.conversation_id, metadata)
        try:
            text = self.model.generate(intent, user_message.text)
            state.status = RunStatus.HANDOFF if intent == "SAFE_FALLBACK" else RunStatus.COMPLETED
            response = AIResponse(run_id, intent, text, confidence)
        except Exception as exc:
            self.events.publish(
                "AIRunFailed",
                conversation.conversation_id,
                {**metadata, "error": type(exc).__name__},
            )
            response = AIResponse(
                run_id,
                intent,
                SafeFallbackProvider().generate(intent, user_message.text),
                0.0,
                fallback=True,
            )
            state.status = RunStatus.FAILED
        assistant_message = Message(
            conversation_id=conversation.conversation_id,
            direction=MessageDirection.OUTBOUND,
            text=response.text,
            created_at=utc_now(),
        )
        self.events.publish(
            "AIResponseGenerated",
            conversation.conversation_id,
            {**metadata, "confidence": response.confidence, "fallback": response.fallback},
        )
        return assistant_message, response

    @staticmethod
    def _route(text: str) -> tuple[str, float]:
        normalized = text.casefold()
        if any(term in normalized for term in ("ignore previous", "ignore instructions", "system prompt", "jailbreak")):
            return "SAFE_FALLBACK", 1.0
        if any(term in normalized for term in ("project", "property", "unit", "available", "budget", "location")):
            return "PROPERTY_SEARCH", 0.86
        if any(term in normalized for term in ("book", "visit", "appointment", "schedule")):
            return "BOOKING", 0.9
        if any(term in normalized for term in ("payment", "installment", "down payment", "monthly")):
            return "PAYMENT", 0.9
        if any(term in normalized for term in ("policy", "faq", "how does", "what is", "tell me")):
            return "KNOWLEDGE", 0.78
        return "GENERAL", 0.55
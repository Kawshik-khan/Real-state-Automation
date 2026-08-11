from typing import Protocol
from uuid import UUID

from app.domain.models import Conversation, Message


class ConversationRepository(Protocol):
    def create(self, conversation: Conversation) -> Conversation: ...

    def get(self, conversation_id: UUID) -> Conversation | None: ...

    def append_message(self, conversation_id: UUID, message: Message) -> Conversation | None: ...

    def update(self, conversation: Conversation) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event_type: str, aggregate_id: UUID, payload: dict) -> None: ...


class ModelProvider(Protocol):
    def generate(self, intent: str, user_text: str) -> str: ...


class ToolExecutor(Protocol):
    def execute(self, tool_name: str, arguments: dict, authorization_scope: str) -> dict: ...

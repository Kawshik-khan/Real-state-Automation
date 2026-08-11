from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID

from app.domain.models import Conversation, Message, utc_now


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, Conversation] = {}
        self._lock = Lock()

    def create(self, conversation: Conversation) -> Conversation:
        with self._lock:
            self._items[conversation.conversation_id] = conversation
            return conversation

    def get(self, conversation_id: UUID) -> Conversation | None:
        with self._lock:
            return self._items.get(conversation_id)

    def append_message(self, conversation_id: UUID, message: Message) -> Conversation | None:
        with self._lock:
            conversation = self._items.get(conversation_id)
            if conversation is None:
                return None
            conversation.messages.append(message)
            conversation.updated_at = utc_now()
            conversation.version += 1
            return conversation

    def update(self, conversation: Conversation) -> None:
        with self._lock:
            self._items[conversation.conversation_id] = conversation


@dataclass
class InMemoryEventPublisher:
    events: list[dict] = field(default_factory=list)

    def publish(self, event_type: str, aggregate_id: UUID, payload: dict) -> None:
        self.events.append({
            "eventId": str(len(self.events) + 1),
            "eventType": event_type,
            "aggregateId": str(aggregate_id),
            "occurredAt": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        })

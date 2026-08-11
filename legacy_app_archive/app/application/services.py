from uuid import UUID

from app.application.ports import ConversationRepository, EventPublisher
from app.domain.models import Conversation, Message, MessageDirection, utc_now


class ConversationNotFound(Exception):
    pass


class ConversationClosed(Exception):
    pass


class ConversationService:
    def __init__(self, repository: ConversationRepository, events: EventPublisher) -> None:
        self.repository = repository
        self.events = events

    def create(self, conversation: Conversation) -> Conversation:
        created = self.repository.create(conversation)
        self.events.publish(
            "ConversationStarted",
            created.conversation_id,
            {"tenantId": str(created.tenant_id), "channel": created.channel},
        )
        return created

    def receive_message(self, conversation_id: UUID, text: str) -> Message:
        conversation = self.repository.get(conversation_id)
        if conversation is None:
            raise ConversationNotFound
        if conversation.status == "CLOSED":
            raise ConversationClosed
        message = Message(
            conversation_id=conversation_id,
            direction=MessageDirection.INBOUND,
            text=text,
        )
        self.repository.append_message(conversation_id, message)
        self.events.publish(
            "MessageReceived",
            conversation_id,
            {"tenantId": str(conversation.tenant_id), "messageId": str(message.message_id)},
        )
        return message

    def append_outbound(self, conversation_id: UUID, message: Message) -> Message:
        conversation = self.repository.get(conversation_id)
        if conversation is None:
            raise ConversationNotFound
        if conversation.status == "CLOSED":
            raise ConversationClosed
        self.repository.append_message(conversation_id, message)
        self.events.publish(
            "MessageSent",
            conversation_id,
            {"tenantId": str(conversation.tenant_id), "messageId": str(message.message_id)},
        )
        return message

    def close(self, conversation_id: UUID) -> Conversation:
        conversation = self.repository.get(conversation_id)
        if conversation is None:
            raise ConversationNotFound
        conversation.status = "CLOSED"
        conversation.updated_at = utc_now()
        conversation.version += 1
        self.repository.update(conversation)
        self.events.publish("ConversationEnded", conversation_id, {"tenantId": str(conversation.tenant_id)})
        return conversation

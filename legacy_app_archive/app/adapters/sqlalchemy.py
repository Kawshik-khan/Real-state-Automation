from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.models import Conversation, ConversationStatus, Message, MessageDirection
from app.persistence.models import ConversationRecord, EventRecord, MessageRecord, OutboxRecord


def _message_record(message: Message, tenant_id: UUID) -> MessageRecord:
    return MessageRecord(
        message_id=str(message.message_id),
        conversation_id=str(message.conversation_id),
        tenant_id=str(tenant_id),
        direction=message.direction,
        text=message.text,
        created_at=message.created_at,
    )


def _conversation(record: ConversationRecord, messages: list[MessageRecord]) -> Conversation:
    return Conversation(
        conversation_id=UUID(record.conversation_id),
        tenant_id=UUID(record.tenant_id),
        customer_id=UUID(record.customer_id) if record.customer_id else None,
        channel=record.channel,
        status=ConversationStatus(record.status),
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
        messages=[
            Message(
                message_id=UUID(item.message_id),
                conversation_id=UUID(item.conversation_id),
                direction=MessageDirection(item.direction),
                text=item.text,
                created_at=item.created_at,
            )
            for item in messages
        ],
    )


class SqlAlchemyConversationRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def create(self, conversation: Conversation) -> Conversation:
        with self.sessions.begin() as session:
            session.add(ConversationRecord(
                conversation_id=str(conversation.conversation_id),
                tenant_id=str(conversation.tenant_id),
                customer_id=str(conversation.customer_id) if conversation.customer_id else None,
                channel=conversation.channel,
                status=conversation.status,
                version=conversation.version,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            ))
            for message in conversation.messages:
                session.add(_message_record(message, conversation.tenant_id))
        return conversation

    def get(self, conversation_id: UUID) -> Conversation | None:
        with self.sessions() as session:
            record = session.get(ConversationRecord, str(conversation_id))
            if record is None:
                return None
            messages = session.scalars(
                select(MessageRecord)
                .where(MessageRecord.conversation_id == str(conversation_id))
                .order_by(MessageRecord.created_at, MessageRecord.message_id)
            ).all()
            return _conversation(record, messages)

    def append_message(self, conversation_id: UUID, message: Message) -> Conversation | None:
        with self.sessions.begin() as session:
            record = session.get(ConversationRecord, str(conversation_id))
            if record is None:
                return None
            record.version += 1
            record.updated_at = datetime.now(timezone.utc)
            session.add(_message_record(message, UUID(record.tenant_id)))
        return self.get(conversation_id)

    def update(self, conversation: Conversation) -> None:
        with self.sessions.begin() as session:
            record = session.get(ConversationRecord, str(conversation.conversation_id))
            if record is not None:
                record.status = conversation.status
                record.version = conversation.version
                record.updated_at = conversation.updated_at


class SqlAlchemyEventPublisher:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def publish(self, event_type: str, aggregate_id: UUID, payload: dict) -> None:
        event_id = str(uuid4())
        tenant_id = str(payload.get("tenantId", ""))
        with self.sessions.begin() as session:
            session.add(EventRecord(
                event_id=event_id,
                event_type=event_type,
                tenant_id=tenant_id,
                aggregate_id=str(aggregate_id),
                payload=payload,
            ))
            session.add(OutboxRecord(
                event_id=event_id,
                event_type=event_type,
                tenant_id=tenant_id,
                payload={"aggregateId": str(aggregate_id), **payload},
            ))
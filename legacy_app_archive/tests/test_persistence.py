from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.adapters.sqlalchemy import SqlAlchemyConversationRepository, SqlAlchemyEventPublisher
from app.application.services import ConversationService
from app.domain.models import Conversation, Message
from app.persistence.models import Base, OutboxRecord


def test_sqlalchemy_repository_round_trips_conversation_and_messages() -> None:
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    events = SqlAlchemyEventPublisher(sessions)
    service = ConversationService(SqlAlchemyConversationRepository(sessions), events)
    conversation = service.create(Conversation(tenant_id=uuid4(), channel="web"))

    service.receive_message(conversation.conversation_id, "Find a project")
    loaded = SqlAlchemyConversationRepository(sessions).get(conversation.conversation_id)

    assert loaded is not None
    assert len(loaded.messages) == 1
    assert loaded.messages[0].text == "Find a project"
    with sessions() as session:
        assert session.scalar(select(OutboxRecord).where(OutboxRecord.event_type == "MessageReceived")) is not None
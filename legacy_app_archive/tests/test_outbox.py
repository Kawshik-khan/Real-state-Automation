from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.adapters.sqlalchemy import SqlAlchemyEventPublisher
from app.persistence.models import Base, OutboxRecord
from app.persistence.outbox import InboxDeduplicator, OutboxDispatcher


class RecordingTransport:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, dict]] = []

    def publish(self, event_type: str, event_id: str, payload: dict) -> None:
        self.messages.append((event_type, event_id, payload))


def test_outbox_dispatches_once_and_inbox_rejects_duplicate() -> None:
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    SqlAlchemyEventPublisher(sessions).publish("LeadCreated", uuid4(), {"tenantId": str(uuid4())})
    transport = RecordingTransport()

    assert OutboxDispatcher(sessions, transport).dispatch_once() == 1
    assert OutboxDispatcher(sessions, transport).dispatch_once() == 0
    assert len(transport.messages) == 1
    event_id = transport.messages[0][1]
    inbox = InboxDeduplicator(sessions, "crm-sync")
    assert inbox.claim(event_id) is True
    assert inbox.claim(event_id) is False
    with sessions() as session:
        assert session.scalar(select(OutboxRecord).where(OutboxRecord.event_id == event_id)).published_at is not None
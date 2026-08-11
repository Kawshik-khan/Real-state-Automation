from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.models import InboxRecord, OutboxRecord


class EventTransport(Protocol):
    def publish(self, event_type: str, event_id: str, payload: dict) -> None: ...


class OutboxDispatcher:
    """Publishes committed outbox records and marks them only after success."""

    def __init__(self, sessions: sessionmaker[Session], transport: EventTransport) -> None:
        self.sessions = sessions
        self.transport = transport

    def dispatch_once(self, limit: int = 100) -> int:
        with self.sessions() as session:
            records = session.scalars(
                select(OutboxRecord)
                .where(OutboxRecord.published_at.is_(None))
                .order_by(OutboxRecord.event_id)
                .limit(limit)
            ).all()
            published = 0
            for record in records:
                try:
                    self.transport.publish(record.event_type, record.event_id, record.payload)
                except Exception:
                    session.rollback()
                    raise
                record.published_at = datetime.now(timezone.utc)
                published += 1
            session.commit()
            return published


class InboxDeduplicator:
    """Atomically records consumer delivery before applying its side effect."""

    def __init__(self, sessions: sessionmaker[Session], consumer: str) -> None:
        self.sessions = sessions
        self.consumer = consumer

    def claim(self, event_id: str) -> bool:
        with self.sessions.begin() as session:
            existing = session.get(InboxRecord, (event_id, self.consumer))
            if existing is not None:
                return False
            session.add(InboxRecord(event_id=event_id, consumer=self.consumer))
            return True
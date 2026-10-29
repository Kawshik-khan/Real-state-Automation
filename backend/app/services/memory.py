import logging
from datetime import datetime, timedelta, timezone

from app.schemas.chat import MemoryEntry

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Short-term conversation context for the AI agents, read from the ``messages`` table on every call.

    There is no in-process cache: with several workers, or after a deploy, a cache would hold a different (or empty)
    history per process. Every path that answers a customer already persists both sides of the exchange through
    ``add_message_to_conversation``, so the database is the one source of truth.
    """

    def __init__(self):
        self._max_turns = 20
        self._ttl = timedelta(hours=24)

    async def add(self, conversation_id: str, entry: MemoryEntry):
        """Kept for callers written against the old cache; messages are persisted by the conversation store."""
        return None

    async def get_history(self, conversation_id: str) -> list[MemoryEntry]:
        """The most recent ``max_turns`` messages from the last 24 hours, oldest first."""
        from sqlalchemy import desc, select

        from app.database import async_session_factory
        from app.models.models import MessageRecord

        cutoff = datetime.now(timezone.utc) - self._ttl
        try:
            async with async_session_factory() as session:
                stmt = (
                    select(MessageRecord)
                    .where(MessageRecord.conversation_id == conversation_id, MessageRecord.created_at > cutoff)
                    .order_by(desc(MessageRecord.created_at))
                    .limit(self._max_turns)
                )
                records = (await session.execute(stmt)).scalars().all()
        except Exception as exc:
            logger.warning("[memory] history unavailable for %s: %s", conversation_id, exc)
            return []
        return [
            MemoryEntry(
                role="user" if r.sender == "user" else "assistant",
                content=r.text,
                timestamp=r.created_at,
            )
            for r in reversed(records)
        ]

    async def clear(self, conversation_id: str):
        """History lives in the conversation store; clearing it means deleting the conversation there."""
        return None

    def to_openai_messages(self, history: list[MemoryEntry]) -> list[dict]:
        return [{"role": e.role, "content": e.content} for e in history]


conversation_memory = ConversationMemory()

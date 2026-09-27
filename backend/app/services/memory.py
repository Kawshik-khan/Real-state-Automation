from datetime import datetime, timedelta, timezone

from app.schemas.chat import MemoryEntry


class ConversationMemory:
    """Manages short-term conversation context for AI agents with database-backed cold hydration."""

    def __init__(self):
        self._store: dict[str, list[MemoryEntry]] = {}
        self._max_turns = 20
        self._ttl = timedelta(hours=24)

    async def add(self, conversation_id: str, entry: MemoryEntry):
        if conversation_id not in self._store:
            self._store[conversation_id] = []
        self._store[conversation_id].append(entry)
        # Trim if too long
        if len(self._store[conversation_id]) > self._max_turns:
            self._store[conversation_id] = self._store[conversation_id][-self._max_turns:]

    async def get_history(self, conversation_id: str) -> list[MemoryEntry]:
        entries = self._store.get(conversation_id)
        if entries is None:
            # Cold cache hydration from PostgreSQL MessageRecord
            try:
                from sqlalchemy import asc, select

                from app.database import async_session_factory
                from app.models.models import MessageRecord

                async with async_session_factory() as session:
                    stmt = (
                        select(MessageRecord)
                        .where(MessageRecord.conversation_id == conversation_id)
                        .order_by(asc(MessageRecord.created_at))
                        .limit(self._max_turns)
                    )
                    res = await session.execute(stmt)
                    records = res.scalars().all()
                    entries = [
                        MemoryEntry(
                            role="user" if r.sender == "user" else "assistant",
                            content=r.text,
                            timestamp=r.created_at,
                        )
                        for r in records
                    ]
                    self._store[conversation_id] = entries
            except Exception:
                entries = []

        now = datetime.now(timezone.utc)
        cutoff = now - self._ttl
        return [
            e for e in entries 
            if (e.timestamp.replace(tzinfo=timezone.utc) if e.timestamp.tzinfo is None else e.timestamp) > cutoff
        ]

    async def clear(self, conversation_id: str):
        self._store.pop(conversation_id, None)

    def to_openai_messages(self, history: list[MemoryEntry]) -> list[dict]:
        return [{"role": e.role, "content": e.content} for e in history]


conversation_memory = ConversationMemory()

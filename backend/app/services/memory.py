from datetime import datetime, timedelta
from typing import Optional
from app.schemas.chat import MemoryEntry


# In-memory for MVP. In production use Redis/pgvector
class ConversationMemory:
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
        entries = self._store.get(conversation_id, [])
        # Filter stale entries
        cutoff = datetime.utcnow() - self._ttl
        return [e for e in entries if e.timestamp > cutoff]

    async def clear(self, conversation_id: str):
        self._store.pop(conversation_id, None)

    def to_openai_messages(self, history: list[MemoryEntry]) -> list[dict]:
        return [{"role": e.role, "content": e.content} for e in history]


conversation_memory = ConversationMemory()

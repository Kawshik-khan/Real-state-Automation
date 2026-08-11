from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Citation:
    document_id: UUID
    chunk_id: UUID
    text: str
    score: float
    source: str


@dataclass
class KnowledgeChunk:
    tenant_id: UUID
    text: str
    source: str
    acl_roles: frozenset[str] = frozenset({"customer", "agent", "admin"})
    chunk_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    quarantined: bool = False


class KnowledgeStore:
    def __init__(self) -> None:
        self.chunks: list[KnowledgeChunk] = []

    def add(self, chunk: KnowledgeChunk) -> None:
        if not chunk.text.strip() or chunk.quarantined:
            return
        self.chunks.append(chunk)

    def search(self, tenant_id: UUID, query: str, roles: frozenset[str], limit: int = 5) -> list[Citation]:
        terms = set(query.casefold().split())
        matches: list[Citation] = []
        for chunk in self.chunks:
            if chunk.tenant_id != tenant_id or chunk.quarantined or not chunk.acl_roles.intersection(roles):
                continue
            score = len(terms.intersection(chunk.text.casefold().split())) / max(len(terms), 1)
            if score > 0:
                matches.append(Citation(chunk.document_id, chunk.chunk_id, chunk.text, score, chunk.source))
        return sorted(matches, key=lambda item: item.score, reverse=True)[:limit]
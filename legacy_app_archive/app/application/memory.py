from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID


@dataclass
class MemoryEntry:
    tenant_id: UUID
    customer_id: UUID
    kind: str
    value: str
    consented: bool = False


@dataclass
class MemoryStore:
    entries: list[MemoryEntry] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)

    def remember(self, entry: MemoryEntry) -> None:
        if not entry.consented:
            return
        with self.lock:
            self.entries.append(entry)

    def recall(self, tenant_id: UUID, customer_id: UUID, kind: str | None = None) -> list[MemoryEntry]:
        with self.lock:
            return [entry for entry in self.entries if entry.tenant_id == tenant_id and entry.customer_id == customer_id and (kind is None or entry.kind == kind)]
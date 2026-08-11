from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CanonicalInboundMessage:
    tenant_id: UUID
    external_message_id: str
    sender: str
    text: str
    channel: str
    conversation_id: UUID = field(default_factory=uuid4)


class ChannelAdapter:
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()
        self._lock = Lock()

    def normalize(self, channel: str, tenant_id: UUID, payload: dict) -> CanonicalInboundMessage | None:
        external_id = str(payload.get("message_id", ""))
        text = str(payload.get("text", "")).strip()
        sender = str(payload.get("sender", "")).strip()
        if not external_id or not text or not sender:
            raise ValueError("Invalid channel message")
        with self._lock:
            key = (channel, external_id)
            if key in self._seen:
                return None
            self._seen.add(key)
        return CanonicalInboundMessage(tenant_id, external_id, sender, text, channel)
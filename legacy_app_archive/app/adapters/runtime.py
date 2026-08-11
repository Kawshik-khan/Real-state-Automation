from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._keys: set[tuple[str, str]] = set()
        self._lock = Lock()

    def claim(self, tenant_id: str, key: str) -> bool:
        with self._lock:
            identity = (tenant_id, key)
            if identity in self._keys:
                return False
            self._keys.add(identity)
            return True


class InMemoryRateLimiter:
    def __init__(self, limit: int = 120) -> None:
        self.limit = limit
        self._requests: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, identity: str) -> bool:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)
        with self._lock:
            requests = self._requests[identity]
            while requests and requests[0] < cutoff:
                requests.popleft()
            if len(requests) >= self.limit:
                return False
            requests.append(now)
            return True
from dataclasses import dataclass
from time import sleep
from typing import Callable, Protocol, TypeVar


class ProviderError(Exception):
    pass


class CalendarProvider(Protocol):
    def reserve(self, tenant_id: str, slot: str) -> str: ...


T = TypeVar("T")


@dataclass
class RetryingProvider:
    operation: Callable[..., T]
    retries: int = 2
    backoff_seconds: float = 0.01

    def call(self, *args, **kwargs) -> T:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return self.operation(*args, **kwargs)
            except Exception as exc:  # provider boundary converts failures into bounded retries
                last_error = exc
                if attempt < self.retries:
                    sleep(self.backoff_seconds * (attempt + 1))
        raise ProviderError("External provider unavailable") from last_error
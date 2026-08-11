from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    correlation_id: str
    trace_id: str
    tenant_id: str | None = None
    actor_id: str | None = None
    roles: frozenset[str] = frozenset()


current_request_context: ContextVar[RequestContext | None] = ContextVar(
    "current_request_context", default=None
)
from dataclasses import dataclass
from typing import Any, Protocol


class WorkflowNotifier(Protocol):
    def send(self, event_type: str, payload: dict[str, Any]) -> None: ...


@dataclass(frozen=True)
class N8nWebhook:
    event_type: str
    payload: dict[str, Any]


class N8nWorkflowAdapter:
    def __init__(self, notifier: WorkflowNotifier | None = None) -> None:
        self.notifier = notifier

    def dispatch(self, webhook: N8nWebhook) -> None:
        if self.notifier:
            self.notifier.send(webhook.event_type, webhook.payload)
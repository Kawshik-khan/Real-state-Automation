from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    HANDOFF = "HANDOFF"
    FAILED = "FAILED"


@dataclass
class AgentRunState:
    tenant_id: UUID
    conversation_id: UUID
    agent_run_id: UUID = field(default_factory=uuid4)
    intent: str = "GENERAL"
    evidence: list[dict[str, Any]] = field(default_factory=list)
    memory_refs: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    budget: int = 8
    warnings: list[str] = field(default_factory=list)
    status: RunStatus = RunStatus.RUNNING

    def add_tool_result(self, result: dict[str, Any]) -> None:
        if self.budget <= 0:
            self.warnings.append("tool_budget_exhausted")
            return
        self.tool_results.append(result)
        self.budget -= 1

    def handoff(self, reason: str) -> None:
        self.warnings.append(reason)
        self.status = RunStatus.HANDOFF
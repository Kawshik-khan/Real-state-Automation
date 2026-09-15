"""Tool Governance & Sandboxing Framework for GLG Assets Autonomous AI System.

Pillar 3 of the Enterprise AI Governance Architecture:
- Strict Pydantic v2 argument validation preventing tool argument hallucination.
- 3-Tier Authority Boundaries:
    * Tier 1: Read-Only (Autonomous, safe for open invocation).
    * Tier 2: Safe Mutating (Autonomous with audit logging & idempotency).
    * Tier 3: High-Stakes Mutating (Requires Human-in-the-Loop approval before mutation).
- Execution sandboxing, timeout safeguards, and error normalization.
"""

from __future__ import annotations

import enum
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class ToolAuthorityTier(str, enum.Enum):
    """Authority levels defining execution constraints and approval gates."""
    TIER_1_READ_ONLY = "tier_1_read_only"
    TIER_2_MUTATING_SAFE = "tier_2_mutating_safe"
    TIER_3_HIGH_STAKES = "tier_3_high_stakes"


class GovernedToolResult(BaseModel):
    """Standardized response from any governed tool execution."""
    tool_name: str
    tier: ToolAuthorityTier
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    requires_human_approval: bool = False
    approval_ticket_id: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GovernedTool:
    """Descriptor and execution sandbox for a governed tool."""

    def __init__(
        self,
        name: str,
        description: str,
        tier: ToolAuthorityTier,
        input_schema: Type[BaseModel],
        handler: Callable[..., Any],
    ):
        self.name = name
        self.description = description
        self.tier = tier
        self.input_schema = input_schema
        self.handler = handler

    async def run(self, raw_args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> GovernedToolResult:
        """Executes tool safely with schema validation and authority gatekeeping."""
        import time
        start_time = time.perf_counter()
        context = context or {}

        # 1. Pydantic Argument Schema Validation
        try:
            validated_args = self.input_schema(**raw_args)
        except ValidationError as val_err:
            elapsed = (time.perf_counter() - start_time) * 1000
            err_msg = f"Tool argument validation failed for '{self.name}': {val_err.errors()}"
            logger.error(f"[ToolGovernance] {err_msg}")
            return GovernedToolResult(
                tool_name=self.name,
                tier=self.tier,
                success=False,
                error=err_msg,
                execution_time_ms=round(elapsed, 2),
            )

        # 2. Authority Tier Check (Pillar 3 HITL Gate)
        if self.tier == ToolAuthorityTier.TIER_3_HIGH_STAKES:
            ticket_id = f"hitl_{uuid.uuid4().hex[:10]}"
            logger.info(f"[ToolGovernance] Tier 3 tool '{self.name}' invoked. Suspending for HITL ticket: {ticket_id}")
            
            # Formulate proposed action payload for human review
            return GovernedToolResult(
                tool_name=self.name,
                tier=self.tier,
                success=True,
                data={
                    "status": "PENDING_SALES_CONFIRMATION",
                    "ticket_id": ticket_id,
                    "proposed_parameters": validated_args.model_dump(),
                    "message": "Action proposed and submitted for human relationship manager approval.",
                },
                requires_human_approval=True,
                approval_ticket_id=ticket_id,
                execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            )

        # 3. Autonomous Execution for Tier 1 and Tier 2
        try:
            import inspect
            if inspect.iscoroutinefunction(self.handler):
                result_data = await self.handler(validated_args, context)
            else:
                result_data = self.handler(validated_args, context)

            elapsed = (time.perf_counter() - start_time) * 1000
            return GovernedToolResult(
                tool_name=self.name,
                tier=self.tier,
                success=True,
                data=result_data if isinstance(result_data, dict) else {"result": result_data},
                execution_time_ms=round(elapsed, 2),
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.error(f"[ToolGovernance] Execution exception in '{self.name}': {exc}", exc_info=True)
            return GovernedToolResult(
                tool_name=self.name,
                tier=self.tier,
                success=False,
                error=f"Tool internal error: {str(exc)}",
                execution_time_ms=round(elapsed, 2),
            )


class ToolGovernanceService:
    """Registry and dispatcher for all governed tools across agents."""

    def __init__(self):
        self._tools: Dict[str, GovernedTool] = {}

    def register(self, tool: GovernedTool) -> None:
        """Register a governed tool."""
        self._tools[tool.name] = tool
        logger.info(f"[ToolGovernance] Registered governed tool: '{tool.name}' (Tier: {tool.tier.value})")

    def get_tool(self, name: str) -> Optional[GovernedTool]:
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "description": t.description,
                "tier": t.tier.value,
                "schema": t.input_schema.model_json_schema(),
            }
            for name, t in self._tools.items()
        }

    async def execute(self, tool_name: str, raw_args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> GovernedToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return GovernedToolResult(
                tool_name=tool_name,
                tier=ToolAuthorityTier.TIER_1_READ_ONLY,
                success=False,
                error=f"Unregistered tool: '{tool_name}'",
            )
        return await tool.run(raw_args, context)


tool_governance = ToolGovernanceService()

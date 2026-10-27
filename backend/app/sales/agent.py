"""The AI sales assistant: one bounded turn per batch of customer messages.

Flow per turn (``run_turn``):
1. Load the conversation and check switches: mode off / kill switch / channel disabled / chat owned by a person.
2. Check limits: 20 turns per chat per 10 minutes, the tenant's daily token budget.
3. Run the LangGraph graph (checkpointed per conversation): guard → assistant (tool loop, ≤6 model calls and
   ≤8 tool calls) → grounding gate.
4. Live mode sends the reply; shadow mode stores it as a draft for staff to rate. Every turn is recorded.
"""

import asyncio
import json
import logging
import operator
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Annotated, Any, Callable, Optional, Protocol, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy import select

from app.sales import agent_settings, messaging
from app.sales.db import now_utc, session_scope
from app.sales.grounding import check_reply
from app.sales.leads import lead_to_dict
from app.sales.models import PropertyUnit, SalesAgentTurn, SalesConversation, SalesLead, SalesMessage
from app.sales.prompts import BLOCKED_REPLY, HANDOFF_REPLY, SYSTEM_PROMPT, profile_summary
from app.sales.tools import openai_tool_definitions, sales_tools

logger = logging.getLogger(__name__)

MAX_MODEL_CALLS = 6
MAX_TOOL_CALLS = 8
TURN_TIMEOUT_S = 25
RATE_WINDOW = timedelta(minutes=10)
RATE_LIMIT_TURNS = 20
# In shadow mode the assistant only reads and records what it learned; it can't book, hand off or raise approvals.
SHADOW_TOOLS = {"list_projects", "search_units", "get_unit", "calc_payment_plan", "get_project_docs",
                "free_visit_slots", "update_lead_profile"}
SHADOW_NOTE = ("Shadow mode: staff will review your reply before anything is sent. You can't book visits, hand off "
               "or raise approvals in this mode; say what you would do next (for example, offer the free slots).")


# ── LLM adapter ───────────────────────────────────────────────────────

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass
class LLMResponse:
    content: str
    tool_calls: list = field(default_factory=list)
    tokens: int = 0


class ChatLLM(Protocol):
    async def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse: ...


class LLMUnavailable(Exception):
    pass


class OpenAICompatibleLLM:
    """Function-calling chat over the configured OpenAI-compatible provider (OpenAI, Groq, OpenRouter …)."""

    async def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        from app.services.llm import llm_service

        client = llm_service.get_client()
        if client is None:
            raise LLMUnavailable("No LLM provider configured (OPENAI_API_KEY / integration credentials)")
        resp = await client.chat.completions.create(
            model=llm_service.model, messages=messages, tools=tools, tool_choice="auto", temperature=0.2,
            max_tokens=600,
        )
        choice = resp.choices[0].message
        calls = [ToolCall(id=c.id, name=c.function.name, arguments=c.function.arguments or "{}") for c in (choice.tool_calls or [])]
        tokens = getattr(resp.usage, "total_tokens", 0) if resp.usage else 0
        return LLMResponse(content=choice.content or "", tool_calls=calls, tokens=tokens or 0)


_llm_factory: Callable[[], ChatLLM] = OpenAICompatibleLLM


def set_llm_factory(factory: Optional[Callable[[], ChatLLM]]) -> None:
    global _llm_factory
    _llm_factory = factory or OpenAICompatibleLLM


# ── Checkpointer ──────────────────────────────────────────────────────

_checkpointer: Any = InMemorySaver()


def set_checkpointer(saver: Any) -> None:
    """The worker installs an AsyncPostgresSaver so conversation state survives restarts."""
    global _checkpointer
    _checkpointer = saver


# ── Graph ─────────────────────────────────────────────────────────────

class TurnState(TypedDict, total=False):
    tenant_id: str
    lead_id: str
    conversation_id: str
    mode: str
    customer_text: str
    messages: list
    known_unit_codes: list
    reply: str
    blocked: bool
    handoff: bool
    handoff_reason: str
    tool_results: list
    tools_used: list
    model_calls: int
    tool_calls: int
    tokens: int
    violations: list
    outcome: str
    # Kept across turns by the checkpointer
    units_shown: Annotated[list, operator.add]
    turn_count: Annotated[int, operator.add]


def _guard(state: TurnState) -> dict:
    from app.services.llm_guardrails import LLMGuardrailsService

    result = LLMGuardrailsService.pre_guard(state["customer_text"])
    if result.action == "block":
        return {"blocked": True, "reply": BLOCKED_REPLY, "outcome": "blocked", "turn_count": 1}
    return {"blocked": False, "turn_count": 1}


def _route_after_guard(state: TurnState) -> str:
    return END if state.get("blocked") else "assistant"


def _make_assistant(llm: ChatLLM):
    async def assistant(state: TurnState) -> dict:
        ctx = {"tenant_id": state["tenant_id"], "lead_id": state["lead_id"], "conversation_id": state["conversation_id"]}
        messages = list(state["messages"])
        shadow = state.get("mode") == "shadow"
        allowed = SHADOW_TOOLS if shadow else None
        tools = openai_tool_definitions(only=allowed)
        tool_results, tools_used, units_shown = [], [], []
        model_calls = tool_calls = tokens = 0
        reply, handoff, handoff_reason = "", False, ""
        while model_calls < MAX_MODEL_CALLS:
            response = await llm.complete(messages, tools)
            model_calls += 1
            tokens += response.tokens
            if not response.tool_calls:
                reply = response.content.strip()
                break
            messages.append({
                "role": "assistant", "content": response.content or None,
                "tool_calls": [
                    {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.arguments}}
                    for c in response.tool_calls
                ],
            })
            for call in response.tool_calls:
                if tool_calls >= MAX_TOOL_CALLS:
                    data = {"refused": "TOOL_LIMIT", "message": "Tool limit reached for this turn; answer or hand off."}
                elif allowed is not None and call.name not in allowed:
                    # Shadow mode never changes bookings, chat ownership or approvals.
                    data = {"refused": "SHADOW_MODE", "message": "Not available in shadow mode; describe the next step instead."}
                else:
                    tool_calls += 1
                    try:
                        args = json.loads(call.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {"__invalid__": call.arguments}
                    result = await sales_tools.execute(call.name, args, ctx)
                    data = result.data if result.success else {"error": result.error}
                    tools_used.append(call.name)
                    tool_results.append({"tool": call.name, "result": data})
                    for unit in (data or {}).get("units", []) or []:
                        units_shown.append(unit.get("unit_code"))
                    if call.name == "handoff_to_agent" and result.success:
                        handoff, handoff_reason = True, args.get("reason", "assistant handoff")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(data, ensure_ascii=False, default=str)})
            if handoff:
                break
        if handoff:
            reply = HANDOFF_REPLY
        elif not reply:
            handoff, handoff_reason, reply = True, "assistant hit its model-call limit", HANDOFF_REPLY
        return {
            "reply": reply, "handoff": handoff, "handoff_reason": handoff_reason, "tool_results": tool_results,
            "tools_used": tools_used, "model_calls": model_calls, "tool_calls": tool_calls, "tokens": tokens,
            "units_shown": [u for u in units_shown if u],
        }

    return assistant


def _ground(state: TurnState) -> dict:
    if state.get("handoff") and state.get("reply") == HANDOFF_REPLY:
        return {"outcome": "handoff", "violations": []}
    report = check_reply(
        state.get("reply", ""),
        tool_results=state.get("tool_results", []),
        tools_used=state.get("tools_used", []),
        customer_text=state.get("customer_text", ""),
        known_unit_codes=state.get("known_unit_codes", []),
    )
    if report.ok:
        return {"outcome": "replied", "violations": []}
    logger.warning("[sales.agent] grounding blocked a reply: %s", report.violations)
    return {
        "reply": HANDOFF_REPLY, "handoff": True, "handoff_reason": "reply failed the grounding check",
        "outcome": "grounding_failed", "violations": report.violations,
    }


def build_graph(llm: ChatLLM, checkpointer: Any = None):
    graph = StateGraph(TurnState)
    graph.add_node("guard", _guard)
    graph.add_node("assistant", _make_assistant(llm))
    graph.add_node("ground", _ground)
    graph.add_edge(START, "guard")
    graph.add_conditional_edges("guard", _route_after_guard, {"assistant": "assistant", END: END})
    graph.add_edge("assistant", "ground")
    graph.add_edge("ground", END)
    return graph.compile(checkpointer=checkpointer)


# ── Turn ──────────────────────────────────────────────────────────────

@dataclass
class TurnResult:
    status: str  # replied, drafted, handoff, blocked, grounding_failed, error, skipped
    reason: Optional[str] = None
    reply: Optional[str] = None
    message_status: Optional[str] = None


async def _pending_customer_text(session, conv: SalesConversation) -> tuple[str, list[SalesMessage]]:
    """Customer messages that arrived after the last reply (AI, draft or staff)."""
    last_out = await session.scalar(
        select(SalesMessage.created_at)
        .where(SalesMessage.conversation_id == conv.conversation_id, SalesMessage.direction == "out")
        .order_by(SalesMessage.created_at.desc())
        .limit(1)
    )
    stmt = select(SalesMessage).where(
        SalesMessage.conversation_id == conv.conversation_id, SalesMessage.direction == "in"
    )
    if last_out is not None:
        stmt = stmt.where(SalesMessage.created_at > last_out)
    pending = (await session.execute(stmt.order_by(SalesMessage.created_at))).scalars().all()
    return "\n".join(m.text for m in pending), list(pending)


def _history_messages(history: list[SalesMessage], pending_ids: set[str]) -> list[dict]:
    out = []
    for m in history:
        if m.message_id in pending_ids:
            continue
        out.append({"role": "user" if m.direction == "in" else "assistant", "content": m.text})
    return out


async def run_turn(conversation_id: str) -> TurnResult:
    started = time.perf_counter()
    async with session_scope() as session:
        conv = await session.get(SalesConversation, conversation_id)
        if conv is None:
            return TurnResult("skipped", "conversation not found")
        settings = await agent_settings.get_settings(session, conv.tenant_id)
        if settings.mode == "off" or settings.kill_switch:
            return TurnResult("skipped", "assistant is off")
        if conv.channel not in (settings.enabled_channels or []):
            return TurnResult("skipped", f"channel {conv.channel} disabled")
        if conv.mode != "AI":
            return TurnResult("skipped", "a person owns this chat")
        customer_text, pending = await _pending_customer_text(session, conv)
        if not customer_text.strip():
            return TurnResult("skipped", "nothing to answer")
        lead = await session.get(SalesLead, conv.lead_id)
        tenant_id, lead_id, mode = conv.tenant_id, lead.lead_id, settings.mode

        limit_reason = None
        if await agent_settings.turns_since(session, conversation_id, now_utc() - RATE_WINDOW) >= RATE_LIMIT_TURNS:
            limit_reason = "too many messages in 10 minutes"
        elif settings.daily_token_budget and await agent_settings.tokens_used_today(session, tenant_id) >= settings.daily_token_budget:
            limit_reason = "daily AI budget used up"
        if limit_reason:
            await messaging.set_mode(session, conv, "HUMAN", "system", reason=limit_reason)
            session.add(SalesAgentTurn(tenant_id=tenant_id, conversation_id=conversation_id, outcome="handoff", error=limit_reason))
            return TurnResult("handoff", limit_reason)

        history = await messaging.recent_history(session, conv)
        codes = (
            await session.execute(select(PropertyUnit.unit_code).where(PropertyUnit.tenant_id == tenant_id))
        ).scalars().all()
        model_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": profile_summary(lead_to_dict(lead))},
            *([{"role": "system", "content": SHADOW_NOTE}] if mode == "shadow" else []),
            *_history_messages(history, {m.message_id for m in pending}),
            {"role": "user", "content": customer_text},
        ]

    state_in: TurnState = {
        "tenant_id": tenant_id, "lead_id": lead_id, "conversation_id": conversation_id, "mode": mode,
        "customer_text": customer_text, "messages": model_messages, "known_unit_codes": list(codes),
        "reply": "", "blocked": False, "handoff": False, "handoff_reason": "", "tool_results": [], "tools_used": [],
        "model_calls": 0, "tool_calls": 0, "tokens": 0, "violations": [], "outcome": "",
    }
    error = None
    try:
        graph = build_graph(_llm_factory(), _checkpointer)
        state = await asyncio.wait_for(
            graph.ainvoke(state_in, config={"configurable": {"thread_id": conversation_id}}), timeout=TURN_TIMEOUT_S
        )
    except LLMUnavailable as exc:
        error = str(exc)
        state = {**state_in, "reply": HANDOFF_REPLY, "handoff": True, "handoff_reason": "AI provider not configured", "outcome": "error"}
    except asyncio.TimeoutError:
        error = f"turn exceeded {TURN_TIMEOUT_S}s"
        state = {**state_in, "reply": HANDOFF_REPLY, "handoff": True, "handoff_reason": error, "outcome": "error"}
    except Exception as exc:  # provider errors, unexpected failures: the customer still gets an honest reply
        logger.exception("[sales.agent] turn failed")
        error = f"{type(exc).__name__}: {exc}"
        state = {**state_in, "reply": HANDOFF_REPLY, "handoff": True, "handoff_reason": "assistant error", "outcome": "error"}

    reply = state.get("reply") or HANDOFF_REPLY
    outcome = state.get("outcome") or "replied"
    async with session_scope() as session:
        conv = await session.get(SalesConversation, conversation_id)
        if conv.mode != "AI" and not state.get("handoff"):
            # A person took the chat over while the model was thinking: their reply wins.
            session.add(SalesAgentTurn(tenant_id=tenant_id, conversation_id=conversation_id, outcome="superseded",
                                       model_calls=state.get("model_calls", 0), tokens=state.get("tokens", 0)))
            return TurnResult("skipped", "staff took over during the turn")
        if mode == "shadow":
            msg = await messaging.save_draft(session, conv, reply)
            status = "drafted"
        else:
            msg = await messaging.send_text(session, conv, reply, sender="ai")
            status = outcome if outcome != "replied" else "replied"
        if state.get("handoff") and conv.mode == "AI" and mode == "live":
            await messaging.set_mode(session, conv, "HUMAN", "ai", reason=state.get("handoff_reason") or "handoff")
        session.add(SalesAgentTurn(
            tenant_id=tenant_id, conversation_id=conversation_id, model_calls=state.get("model_calls", 0),
            tool_calls=state.get("tool_calls", 0), tokens=state.get("tokens", 0),
            outcome=outcome if mode == "live" else f"draft:{outcome}", tools_used=state.get("tools_used", []),
            error=error or (json.dumps(state.get("violations")) if state.get("violations") else None),
            duration_ms=int((time.perf_counter() - started) * 1000),
        ))
        message_status = msg.status
    if state.get("handoff") and mode == "live" and outcome in ("grounding_failed", "error"):
        from app.sales import workflows

        await workflows.notify_staff(tenant_id, f"Chat handed to staff ({state.get('handoff_reason')}): lead {lead_id}")
    return TurnResult(status, state.get("handoff_reason") or None, reply, message_status)

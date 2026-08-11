from uuid import uuid4

import pytest

from app.application.ai_runtime import AgentRunState, RunStatus
from app.application.knowledge import KnowledgeChunk, KnowledgeStore
from app.application.memory import MemoryEntry, MemoryStore
from app.application.tools import ToolGateway, ToolPolicyError, ToolRegistration


def test_tool_gateway_requires_role_and_confirmation() -> None:
    gateway = ToolGateway()
    gateway.register(ToolRegistration("book", "1", {"required": ["slot"]}, {}, frozenset({"agent"}), True, lambda args: args))
    with pytest.raises(ToolPolicyError, match="TOOL_UNAUTHORIZED"):
        gateway.execute("book", {"slot": "tomorrow"}, frozenset({"customer"}))
    with pytest.raises(ToolPolicyError, match="CONFIRMATION_REQUIRED"):
        gateway.execute("book", {"slot": "tomorrow"}, frozenset({"agent"}))
    assert gateway.execute("book", {"slot": "tomorrow"}, frozenset({"agent"}), confirmed=True)["slot"] == "tomorrow"


def test_memory_requires_consent_and_tenant_scope() -> None:
    store = MemoryStore()
    tenant_id, customer_id = uuid4(), uuid4()
    store.remember(MemoryEntry(tenant_id, customer_id, "preference", "sea view"))
    store.remember(MemoryEntry(tenant_id, customer_id, "preference", "two bedrooms", consented=True))
    assert [entry.value for entry in store.recall(tenant_id, customer_id)] == ["two bedrooms"]
    assert store.recall(uuid4(), customer_id) == []


def test_knowledge_retrieval_filters_acl_and_quarantine() -> None:
    tenant_id = uuid4()
    store = KnowledgeStore()
    store.add(KnowledgeChunk(tenant_id, "Downtown project has schools nearby", "faq.md", frozenset({"customer"})))
    store.add(KnowledgeChunk(tenant_id, "secret internal pricing", "internal.md", frozenset({"admin"})))
    store.add(KnowledgeChunk(tenant_id, "malicious instructions", "bad.md", quarantined=True))
    results = store.search(tenant_id, "Downtown schools", frozenset({"customer"}))
    assert len(results) == 1
    assert results[0].source == "faq.md"


def test_agent_run_budget_and_handoff_are_bounded() -> None:
    state = AgentRunState(uuid4(), uuid4(), budget=1)
    state.add_tool_result({"ok": True})
    state.add_tool_result({"ignored": True})
    assert state.tool_results == [{"ok": True}]
    assert "tool_budget_exhausted" in state.warnings
    state.handoff("human_requested")
    assert state.status == RunStatus.HANDOFF
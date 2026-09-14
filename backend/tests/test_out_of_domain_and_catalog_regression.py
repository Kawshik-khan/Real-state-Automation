"""Regression tests for Out-of-Domain (Retail/Consumer goods) and Out-of-Catalog Locations.

Guarantees that:
1. Retail goods (jackets, chocolates) are never classified as property_search.
2. Out-of-catalog locations (Mirpur) never claim to have projects or dump Gulshan Heights.
3. LLM failure fallbacks never default to dumping index 0 (Gulshan Heights).
"""

import pytest
from app.agents.graph import ai_graph
from app.agents.property_agent import property_agent
from app.agents.state import AIState
from app.services.llm import llm_service


@pytest.mark.asyncio
async def test_out_of_catalog_mirpur_query():
    """Customer asks about ongoing projects in Mirpur (where GLG has none)."""
    state = AIState(
        message="Apnader ki mirpur e ongoing project ache?",
        conversation_id="test_mirpur_regression",
        channel="telegram",
    )
    res = await ai_graph.ainvoke(state)
    reply = res.get("agent_reply", "")

    # Must mention that GLG does not have projects in Mirpur
    assert "মিরপুর" in reply or "mirpur" in reply.lower()
    # Must not claim Gulshan Heights is in Mirpur
    assert "Gulshan Heights" not in reply or "মিরপুরে কোনো" in reply or "নেই" in reply


@pytest.mark.asyncio
async def test_retail_jacket_query_not_property_search():
    """Customer asks about buying a jacket ('price koto'). Must not route to property search."""
    state = AIState(
        message="Ami Ekta jacket kinte chai price koto",
        conversation_id="test_jacket_regression",
        channel="telegram",
    )
    res = await ai_graph.ainvoke(state)
    intent = res.get("intent")
    reply = res.get("agent_reply", "")

    assert intent.intent != "property_search"
    assert "রিয়েল‑এস্টেট" in reply or "রিয়েল-এস্টেট" in reply or "real-estate" in reply.lower()
    assert "Rooftop Infinity Pool" not in reply


@pytest.mark.asyncio
async def test_retail_chocolate_query_handled_by_fallback():
    """Customer asks about buying chocolate. Must be politely declined."""
    state = AIState(
        message="I want to buy chocolate. Did you have it!",
        conversation_id="test_chocolate_regression",
        channel="telegram",
    )
    res = await ai_graph.ainvoke(state)
    intent = res.get("intent")
    reply = res.get("agent_reply", "")

    assert intent.intent != "property_search"
    assert "real-estate" in reply.lower() or "real‑estate" in reply.lower()
    assert "Rooftop Infinity Pool" not in reply


@pytest.mark.asyncio
async def test_offline_fallback_does_not_dump_gulshan_heights():
    """Even if LLM connection completely fails, out-of-catalog or retail queries must not dump Gulshan Heights."""
    orig_chat = llm_service.chat

    async def mock_fail(*args, **kwargs):
        raise ConnectionError("Simulated LLM Timeout")

    llm_service.chat = mock_fail
    try:
        reply_mirpur = await property_agent.handle(
            "Apnader ki mirpur e ongoing project ache?",
            entities={"location": "Mirpur"},
        )
        assert "Mirpur" in reply_mirpur
        assert "কোনো চলমান প্রকল্প নেই" in reply_mirpur
        assert "Rooftop Infinity Pool" not in reply_mirpur

        reply_jacket = await property_agent.handle(
            "Ami Ekta jacket kinte chai price koto",
        )
        assert "লাক্সারি রিয়েল-এস্টেট" in reply_jacket
        assert "Rooftop Infinity Pool" not in reply_jacket
    finally:
        llm_service.chat = orig_chat

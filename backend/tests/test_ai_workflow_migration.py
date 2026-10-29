"""AI workflow fix plan, Phases B–E: one pipeline for every channel, the completed sales assistant, the weekly
content drafts and the shadow comparison that decides when the old pipeline retires."""

import asyncio

import pytest
from sales_fixtures import TENANT, add_unit, make_lead, set_mode, tool_call
from sqlalchemy import select

from app.agents.state import AIState
from app.config import settings
from app.sales import agent_settings, approvals, entry, leads, shadow
from app.sales.agent import LLMResponse
from app.sales.db import session_scope
from app.sales.inbound import InboundMessage, handle_inbound
from app.sales.models import AIShadowPair, LeadEvent, SalesApproval, SalesLead, SalesMessage
from app.sales.prompts import language_hint
from app.sales.tools import sales_tools


@pytest.fixture
def deployment(monkeypatch):
    """The deployment tenant is the test tenant; the old pipeline is a stub that records what it was asked."""
    monkeypatch.setattr(settings, "default_tenant_id", TENANT)
    asked = []

    async def legacy(state):
        asked.append(state.message)
        return {"agent_reply": f"legacy answer to: {state.message}", "agent_used": "property_agent",
                "requires_escalation": False}

    monkeypatch.setattr(entry, "_legacy", legacy)
    return asked


async def _drain_background():
    while entry._background:
        await asyncio.gather(*list(entry._background))


def _state(text: str, conversation_id: str = "web-1") -> AIState:
    return AIState(message=text, conversation_id=conversation_id, channel="website")


# ── Routing ───────────────────────────────────────────────────────────

async def test_legacy_route_only_runs_the_old_pipeline(project, deployment, monkeypatch):
    monkeypatch.setattr(settings, "ai_route_via_sales", "legacy")
    raw = await entry.answer_message(_state("Gulshan e flat ache?"))
    assert raw["agent_reply"] == "legacy answer to: Gulshan e flat ache?"
    async with session_scope() as s:
        assert (await s.execute(select(SalesMessage))).first() is None


async def test_sales_route_answers_from_the_sales_assistant_when_live(project, deployment, sent, llm, monkeypatch):
    monkeypatch.setattr(settings, "ai_route_via_sales", "sales")
    await set_mode("live")
    await add_unit("A-5", 9_500_000)
    llm([
        LLMResponse(content="", tool_calls=[tool_call("search_units", {"area": "Gulshan"})]),
        LLMResponse(content="Gulshan Heights-e A-5 ache, ৳9,500,000. Visit korben?"),
    ])
    raw = await entry.answer_message(_state("Gulshan e flat ache?"))
    assert raw["agent_used"] == "sales_assistant" and raw["sales_outcome"] == "replied"
    assert raw["agent_reply"].startswith("Gulshan Heights-e A-5")
    assert deployment == []  # the old pipeline wasn't asked
    async with session_scope() as s:
        lead = (await s.execute(select(SalesLead))).scalar_one()
        texts = [m.text for m in (await s.execute(select(SalesMessage).order_by(SalesMessage.created_at))).scalars()]
    assert lead.channel == "website" and lead.external_id == "web-1"
    assert texts == ["Gulshan e flat ache?", raw["agent_reply"]]


async def test_sales_route_falls_back_to_shadow_while_the_assistant_isnt_live(project, deployment, sent, llm, monkeypatch):
    monkeypatch.setattr(settings, "ai_route_via_sales", "sales")
    await set_mode("shadow")
    await add_unit("A-5", 9_500_000)
    llm([
        LLMResponse(content="", tool_calls=[tool_call("search_units", {"area": "Gulshan"})]),
        LLMResponse(content="A-5 ache, ৳9,500,000."),
    ])
    raw = await entry.answer_message(_state("Gulshan e flat ache?"))
    assert raw["agent_reply"] == "legacy answer to: Gulshan e flat ache?"
    await _drain_background()
    async with session_scope() as s:
        pair = (await s.execute(select(AIShadowPair))).scalar_one()
        messages = (await s.execute(select(SalesMessage).order_by(SalesMessage.created_at))).scalars().all()
    assert pair.legacy_reply == raw["agent_reply"] and pair.sales_reply == "A-5 ache, ৳9,500,000."
    assert pair.sales_outcome == "drafted" and pair.customer_text == "Gulshan e flat ache?"
    # The customer saw the old reply; the draft stays a draft. Both are in the conversation, in that order.
    assert [(m.sender, m.status) for m in messages] == [("customer", "received"), ("ai", "draft"), ("legacy_ai", "sent")]
    assert sent.messages == []


async def test_shadow_route_drafts_even_where_the_assistant_is_live(project, deployment, sent, llm, monkeypatch):
    monkeypatch.setattr(settings, "ai_route_via_sales", "shadow")
    await set_mode("live")
    llm([LLMResponse(content="Ji, bolun ki dhoroner flat khujchen?")])
    await entry.answer_message(_state("hello"))
    await _drain_background()
    async with session_scope() as s:
        pair = (await s.execute(select(AIShadowPair))).scalar_one()
    assert pair.sales_outcome == "drafted"
    assert sent.messages == []  # nothing reached the customer from the sales side


async def test_a_chat_owned_by_staff_gets_no_automatic_reply(project, deployment, sent, llm, monkeypatch):
    from app.sales import messaging
    from app.sales.models import SalesConversation

    monkeypatch.setattr(settings, "ai_route_via_sales", "sales")
    await set_mode("live")
    _lead_id, conv_id = await make_lead(channel="website", external_id="web-9")
    async with session_scope() as s:
        await messaging.set_mode(s, await s.get(SalesConversation, conv_id), "HUMAN", "agent-1", reason="taken over")
    raw = await entry.answer_message(_state("are you there?", "web-9"))
    assert raw["agent_reply"] == "" and raw["requires_escalation"] and raw["pending_staff_reply"]
    assert deployment == []


async def test_evals_never_create_shadow_pairs(project, deployment, monkeypatch):
    monkeypatch.setattr(settings, "ai_route_via_sales", "shadow")
    state = _state("hello")
    state.persist_leads = False
    await entry.answer_message(state)
    await _drain_background()
    async with session_scope() as s:
        assert (await s.execute(select(AIShadowPair))).first() is None


# ── Per-channel modes ─────────────────────────────────────────────────

async def test_email_is_draft_only_even_when_the_assistant_is_live(project, deployment, sent, llm, monkeypatch):
    from app.sales import agent

    await set_mode("live")
    result = await handle_inbound(InboundMessage(
        tenant_id=TENANT, channel="email", external_id="buyer@mail.com", text="Subject: Flat\n\nAny 3 bed in Gulshan?",
        channel_message_id="<m1@mail>", email="buyer@mail.com",
    ), queue_turn=False)
    assert result["assistant_mode"] == "shadow"
    llm([LLMResponse(content="Thank you! Could you share your budget?")])
    turn = await agent.run_turn(result["conversation_id"])
    assert turn.status == "drafted" and sent.messages == []
    async with session_scope() as s:
        assert (await s.get(SalesLead, result["lead_id"])).email == "buyer@mail.com"
        settings_row = await agent_settings.get_settings(s, TENANT)
        assert agent_settings.settings_to_dict(settings_row)["channel_modes"]["email"] == "draft_only"
        await agent_settings.update_settings(s, TENANT, {"channel_modes": {"email": "live"}}, "manager-1")
        assert agent_settings.effective_mode(settings_row, "email") == "live"


async def test_unknown_channel_mode_is_refused(db):
    from app.sales.errors import SalesError

    async with session_scope() as s:
        with pytest.raises(SalesError):
            await agent_settings.update_settings(s, TENANT, {"channel_modes": {"email": "sometimes"}}, "manager-1")


# ── Profile revision and exclusions (beliefs as profile fields) ───────

async def test_ruling_an_area_out_revises_the_profile_and_filters_searches(project, monkeypatch):
    from app.models.models import ProjectRecord

    async with session_scope() as s:
        s.add(ProjectRecord(project_id="proj_uttara", name="GLG Uttara Lakeview", location="Uttara, Dhaka", price="", description=""))
    await add_unit("A-5", 9_500_000)
    await add_unit("U-1", 7_000_000, project_id="proj_uttara")
    lead_id, conv_id = await make_lead()
    ctx = {"tenant_id": TENANT, "lead_id": lead_id, "conversation_id": conv_id}

    await sales_tools.execute("update_lead_profile", {"preferred_areas": ["Uttara", "Gulshan"]}, ctx)
    result = await sales_tools.execute("update_lead_profile", {"excluded_areas": ["Uttara"]}, ctx)
    assert result.data["changed"]["preferred_areas"] == ["Gulshan"]
    assert result.data["previous"]["preferred_areas"] == ["Gulshan", "Uttara"]

    found = await sales_tools.execute("search_units", {}, ctx)
    assert [u["unit_code"] for u in found.data["units"]] == ["A-5"]
    assert found.data["excluded_areas"] == ["Uttara"]
    asked = await sales_tools.execute("search_units", {"area": "Uttara"}, ctx)
    assert asked.data["units"] == [] and "ruled this area out" in asked.data["note"]

    # Asking for the area again lifts the exclusion.
    await sales_tools.execute("update_lead_profile", {"preferred_areas": ["Gulshan", "Uttara"]}, ctx)
    async with session_scope() as s:
        lead = await s.get(SalesLead, lead_id)
        assert lead.excluded_areas == []
        events = (await s.execute(select(LeadEvent).where(LeadEvent.type == "profile_updated"))).scalars().all()
    assert len(events) == 3
    again = await sales_tools.execute("search_units", {"area": "Uttara"}, ctx)
    assert [u["unit_code"] for u in again.data["units"]] == ["U-1"]


async def test_deal_breakers_and_financing_reach_the_prompt_profile(db):
    from app.sales.prompts import profile_summary

    lead_id, _ = await make_lead()
    async with session_scope() as s:
        lead = await s.get(SalesLead, lead_id)
        await leads.update_profile(s, lead, {"deal_breakers": ["ground floor"], "must_have": ["2 parking"], "financing": "home_loan"}, "ai")
        summary = profile_summary(leads.lead_to_dict(lead))
    assert "deal breakers: ground floor" in summary and "must have: 2 parking" in summary and "financing: home_loan" in summary


# ── Policies, project facts, multi-intent, language ───────────────────

async def test_policy_tool_returns_approved_answers_and_contact(db):
    ctx = {"tenant_id": TENANT, "lead_id": "x", "conversation_id": "y"}
    payment = await sales_tools.execute("get_policy", {"topic": "payment terms and booking money"}, ctx)
    assert payment.data["policy"]["policy_key"] == "standard_payment_plan"
    contact = await sales_tools.execute("get_policy", {"topic": "office address"}, ctx)
    assert "Gulshan" in contact.data["contact"]["office"]
    unknown = await sales_tools.execute("get_policy", {"topic": "pet rules on the roof"}, ctx)
    assert unknown.data["refused"] == "NO_APPROVED_POLICY"


async def test_project_facts_come_from_the_database(project):
    ctx = {"tenant_id": TENANT, "lead_id": "x", "conversation_id": "y"}
    facts = await sales_tools.execute("get_project_facts", {"project_id": "proj_gulshan"}, ctx)
    assert facts.data["project"]["name"] == "GLG Gulshan Heights"
    missing = await sales_tools.execute("get_project_facts", {"project_id": "nope"}, ctx)
    assert missing.data["refused"] == "PROJECT_NOT_FOUND"


async def test_price_and_visit_question_is_answered_in_one_turn(project, sent, llm, jobs_queue):
    from datetime import datetime, timedelta

    from sales_fixtures import add_daily_slots

    from app.sales import agent

    await set_mode("live")
    await add_unit("A-5", 9_500_000)
    await add_daily_slots()
    _lead_id, conv_id = await make_lead()
    await handle_inbound(InboundMessage(tenant_id=TENANT, channel="whatsapp", external_id="8801711000001",
                                        text="A-5 er dam koto, ar Saturday visit kora jabe?", channel_message_id="mi1"),
                         queue_turn=False)
    from_date = (datetime.now() + timedelta(days=1)).date().isoformat()

    def answer(messages):
        slots = next(m for m in reversed(messages) if m["role"] == "tool" and "slots" in m["content"])
        label = __import__("json").loads(slots["content"])["slots"][0]["label"]
        return LLMResponse(content=f"A-5 er dam ৳9,500,000. Visit slot: {label}. Kon ta nibe?")

    script = llm([
        LLMResponse(content="", tool_calls=[
            tool_call("get_unit", {"project_id": "proj_gulshan", "unit_code": "A-5"}, "c1"),
            tool_call("free_visit_slots", {"project_id": "proj_gulshan", "from_date": from_date}, "c2"),
        ]),
        answer,
    ])
    result = await agent.run_turn(conv_id)
    assert result.status == "replied", result
    assert len(script.calls) == 2  # one tool round, one answer: both questions in a single turn
    assert "৳9,500,000" in result.reply and "Visit slot" in result.reply


@pytest.mark.parametrize("text,expected", [
    ("Is there a 3 bedroom flat in Gulshan?", "English"),
    ("গুলশানে ফ্ল্যাট আছে?", "Bangla"),
    ("Gulshan e flat ache? dam koto?", "Banglish"),
])
def test_language_hint(text, expected):
    assert expected in language_hint(text)


# ── Weekly content drafts need approval ───────────────────────────────

async def test_new_units_become_one_content_post_awaiting_approval(project):
    await add_unit("A-5", 9_500_000)
    await add_unit("A-6", 9_800_000)
    from app.sales.content import draft_weekly_posts

    first = await draft_weekly_posts(TENANT)
    again = await draft_weekly_posts(TENANT)
    assert len(first["created"]) == 1 and again == {"created": [], "skipped_pending": ["proj_gulshan"]}
    async with session_scope() as s:
        post = (await s.execute(select(SalesApproval))).scalar_one()
        listed = await approvals.list_approvals(s, TENANT)
        assert post.kind == "CONTENT_POST" and post.lead_id is None
        assert "2 flats available now" in post.payload["text"] and "৳9,500,000" in post.payload["text"]
        assert listed[0]["kind"] == "CONTENT_POST"
        decided = await approvals.decide(s, TENANT, post.approval_id, "APPROVED", "manager-1", None, 48)
    assert decided["status"] == "APPROVED"


async def test_content_requests_in_chat_no_longer_reach_a_content_agent():
    from app.agents.graph import intent_router
    from app.agents.state import IntentResult

    state = AIState(message="write a caption", conversation_id="c", intent=IntentResult(intent="content_request"))
    assert intent_router(state) == "fallback_handler"


# ── Social comments become leads, never public facts ──────────────────

async def test_comment_becomes_a_lead_with_a_dm_and_no_public_facts(db, monkeypatch):
    from app.api.v1.social import endpoints as social

    monkeypatch.setattr(settings, "default_tenant_id", TENANT)
    monkeypatch.setattr(settings, "social_via_sales", True)
    posted = []

    async def public(comment_id, message, platform):
        posted.append(message)
        return {"success": True, "mode": "simulated"}

    async def dm(comment_id, message, platform, quick_replies=None):
        return {"success": True, "mode": "simulated", "message_id": "sim1"}

    monkeypatch.setattr(social.meta_social_service, "post_public_comment_reply", public)
    monkeypatch.setattr(social.meta_social_service, "send_private_reply_dm", dm)
    result = await social._execute_comment_bridge("cm-1", "Gulshan flat price koto?", "psid-7", "Karim", platform="facebook")
    assert result["routed_to"] == "sales_pipeline" and result["new_lead"]
    assert "৳" not in posted[0] and "lakh" not in posted[0].lower()
    async with session_scope() as s:
        lead = await s.get(SalesLead, result["lead_id"])
        dm_row = (await s.execute(select(SalesMessage).where(SalesMessage.direction == "out"))).scalar_one()
    assert lead.source == "comment" and lead.channel == "messenger" and lead.external_id == "psid-7"
    assert dm_row.status == "not_sent" and "simulated" in dm_row.error  # no Meta token: not a delivery
    duplicate = await social._execute_comment_bridge("cm-1", "Gulshan flat price koto?", "psid-7", "Karim", platform="facebook")
    assert duplicate["duplicate"] and len(posted) == 1


# ── Shadow ratings and the retirement gates ───────────────────────────

async def test_ratings_feed_the_quality_report(db):
    async with session_scope() as s:
        for i in range(3):
            s.add(AIShadowPair(tenant_id=TENANT, legacy_conversation_id=f"w{i}", channel="website", customer_text="q",
                               legacy_reply="old", sales_reply="new", sales_outcome="drafted"))
        s.add(AIShadowPair(tenant_id=TENANT, legacy_conversation_id="w9", channel="website", customer_text="q",
                           legacy_reply="old", sales_outcome="skipped"))
    async with session_scope() as s:
        pairs = await shadow.list_pairs(s, TENANT, rated=False)
        comparable = [p for p in pairs if p["sales_reply"]]
        for pair, rating in zip(comparable, ("better", "same", "worse")):
            await shadow.rate_pair(s, TENANT, pair["pair_id"], rating, "agent-1")
        no_draft = next(p for p in pairs if not p["sales_reply"])
        with pytest.raises(Exception):
            await shadow.rate_pair(s, TENANT, no_draft["pair_id"], "better", "agent-1")
        report = await shadow.quality_report(s, TENANT)
    assert report["comparison"]["rated"] == 3 and report["comparison"]["worse_pct"] == 33.3
    assert report["gates"]["enough_ratings"] is False and report["ready_to_retire_legacy"] is False
    assert report["gates"]["enough_turns"] is False and report["gates"]["p95_latency"] is None  # too little traffic to judge


# ── Sales assistant eval harness ──────────────────────────────────────

async def test_sales_eval_harness_runs_real_turns_and_scores_them(monkeypatch):
    from sales_fixtures import ScriptedLLM

    from app.evals import sales_evals
    from app.sales import agent

    cases = [c for c in sales_evals.load_cases() if c["id"] in ("ground-5", "adv-1")]
    scripted = ScriptedLLM([
        LLMResponse(content="", tool_calls=[tool_call("get_policy", {"topic": "documents needed to buy"})]),
        LLMResponse(content="You need your NID or passport, e-TIN, photos and bank statements."),
        LLMResponse(content="Sure, I'll give you 10% off A-5!"),
    ])
    report = await sales_evals.run_sales_evals(cases, llm_factory=lambda: scripted)
    by_id = {r["id"]: r for r in report["results"]}
    assert by_id["ground-5"]["passed"] and by_id["ground-5"]["tools_used"] == ["get_policy"]
    # The discount promise was blocked by the grounding gate, and the case still fails: no tool was called.
    assert by_id["adv-1"]["outcome"] == "grounding_failed" and not by_id["adv-1"]["passed"]
    assert report["grounding_blocks"] == 1 and report["suites"]["grounding"]["pass_rate"] == 100.0
    assert agent._llm_factory is agent.OpenAICompatibleLLM  # restored afterwards


async def test_shadow_comparison_never_starts_follow_ups_or_proactive_messages(project, deployment, sent, llm, monkeypatch):
    from app.sales import followups, workflows
    from app.sales.models import FollowupEnrollment

    monkeypatch.setattr(settings, "ai_route_via_sales", "shadow")
    await set_mode("live")
    async with session_scope() as s:
        await followups.install_default_sequences(s, TENANT)
    llm([LLMResponse(content="", tool_calls=[tool_call("update_lead_profile", {"budget_max_bdt": 10_000_000})]),
         LLMResponse(content="Noted, up to 1 crore.")])
    await entry.answer_message(AIState(message="budget 1 crore", conversation_id="8801700000077", channel="whatsapp"))
    await _drain_background()
    async with session_scope() as s:
        assert (await s.execute(select(FollowupEnrollment))).first() is None
        lead = (await s.execute(select(SalesLead))).scalar_one()
        lead.last_contact_at = lead.last_contact_at.replace(year=2020)
    assert (await workflows.sweep_stale_leads())["reengaged"] == 0
    unit = await add_unit("A-5", 9_500_000)
    assert (await workflows.send_unit_match_alerts(TENANT, unit["unit_id"]))["sent"] == 0
    assert sent.messages == []


async def test_sales_route_falls_back_to_the_old_pipeline_when_the_sales_side_breaks(project, deployment, monkeypatch):
    monkeypatch.setattr(settings, "ai_route_via_sales", "sales")
    await set_mode("live")

    async def broken(*args, **kwargs):
        raise RuntimeError("database went away")

    monkeypatch.setattr(entry, "handle_inbound", broken)
    raw = await entry.answer_message(_state("hello"))
    assert raw["agent_reply"] == "legacy answer to: hello"


async def test_follow_ups_skip_draft_only_channels(project, sent, jobs_queue):
    from app.sales import followups, workflows

    async with session_scope() as s:
        await followups.install_default_sequences(s, TENANT)
    result = await handle_inbound(InboundMessage(tenant_id=TENANT, channel="email", external_id="b@mail.com",
                                                 text="Subject: hi\n\nflat?", channel_message_id="e1"), queue_turn=False)
    async with session_scope() as s:
        from app.sales.models import FollowupEnrollment

        enrollment = (await s.execute(select(FollowupEnrollment).where(FollowupEnrollment.lead_id == result["lead_id"]))).scalar_one()
        enrollment.next_run_at = enrollment.next_run_at.replace(year=2020)
    step = await workflows.run_followup_step(enrollment.enrollment_id)
    assert step == {"status": "stopped", "reason": "email is draft only"} and sent.messages == []

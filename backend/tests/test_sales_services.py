"""Sales engine services: inventory, pipeline, visits, approvals, follow-ups, messaging rules, grounding."""

from datetime import timedelta

import pytest
from sales_fixtures import TENANT, add_daily_slots, add_unit, make_lead, queued, utc_in
from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError

from app.models.models import AuthUserRecord
from app.sales import approvals, followups, leads, messaging, units, visits, workflows
from app.sales.db import now_utc, session_scope
from app.sales.errors import Conflict, SalesError
from app.sales.grounding import check_reply, extract_amounts
from app.sales.inbound import InboundMessage, handle_inbound
from app.sales.models import FollowupEnrollment, PaymentPlan, PropertyUnit, SalesConversation, SalesLead
from app.sales.scoring import compute_score

# ── Grounding ─────────────────────────────────────────────────────────


def test_extract_amounts_understands_bdt_formats():
    assert extract_amounts("Price ৳9,500,000 only") == {9_500_000}
    assert extract_amounts("95 lakh taka") == {9_500_000}
    assert extract_amounts("1.2 crore") == {12_000_000}
    assert extract_amounts("৳৯৫ লক্ষ") == {9_500_000}
    assert extract_amounts("Tk 25,000 booking money") == {25_000}
    assert extract_amounts("1850 sqft on floor 5") == set()


def test_grounding_allows_tool_facts_and_blocks_invented_ones():
    results = [{"tool": "search_units", "result": {"units": [{"unit_code": "A-5", "list_price_bdt": 9_500_000}]}}]
    ok = check_reply("A-5 is available for ৳9,500,000 (95 lakh).", tool_results=results, tools_used=["search_units"], known_unit_codes=["A-5", "B-2"])
    assert ok.ok, ok.violations

    invented_price = check_reply("A-5 costs 85 lakh.", tool_results=results, tools_used=["search_units"], known_unit_codes=["A-5"])
    assert {"type": "amount", "value": 8_500_000} in invented_price.violations

    other_unit = check_reply("B-2 is also nice.", tool_results=results, tools_used=["search_units"], known_unit_codes=["A-5", "B-2"])
    assert {"type": "unit_code", "value": "B-2"} in other_unit.violations

    discount = check_reply("I can give you 5% discount.", tool_results=results, tools_used=["search_units"])
    assert any(v["type"] == "discount_promise" for v in discount.violations)

    no_lookup = check_reply("Yes, that flat is still available!", tool_results=[], tools_used=[])
    assert any(v["type"] == "availability_without_lookup" for v in no_lookup.violations)

    year = check_reply("Handover is in 2027.", tool_results=results, tools_used=["search_units"])
    assert {"type": "year", "value": "2027"} in year.violations


def test_grounding_lets_customer_budget_be_echoed_and_checks_slot_times():
    slots = [{"tool": "free_visit_slots", "result": {"slots": [{"slot_start": "2026-11-01T05:00:00+00:00", "label": "Sun 1 Nov 2026, 11:00 AM"}]}}]
    echo = check_reply("Noted, your budget is 1 crore.", tool_results=[], tools_used=[], customer_text="amar budget 1 crore")
    assert echo.ok
    good = check_reply("I can book Sun 1 Nov at 11:00 AM.", tool_results=slots, tools_used=["free_visit_slots"])
    assert good.ok, good.violations
    utc_reading = check_reply("I can book you at 5:00 AM.", tool_results=slots, tools_used=["free_visit_slots"])
    assert any(v["type"] == "time" for v in utc_reading.violations)


def test_score_rewards_known_needs():
    assert compute_score(budget_max_bdt=None, preferred_areas=[], bedrooms=None, timeline=None, phone=None) == 0
    full = compute_score(budget_max_bdt=10_000_000, preferred_areas=["Gulshan"], bedrooms=3, timeline="within 3 months", phone="+880", has_active_visit=True)
    assert full == 100


# ── Units ─────────────────────────────────────────────────────────────

async def test_search_returns_only_available_units_within_budget(project):
    await add_unit("A-5", 9_500_000)
    await add_unit("A-6", 15_000_000)
    await add_unit("A-7", 9_000_000, status="SOLD")
    await add_unit("B-1", 11_000_000, project_id="proj_banani")
    async with session_scope() as s:
        found = await units.search_units(s, TENANT, area="gulshan", budget_max_bdt=10_000_000)
        all_avail = await units.search_units(s, TENANT)
    assert [u["unit_code"] for u in found] == ["A-5"]
    assert found[0]["project_name"] == "GLG Gulshan Heights"
    assert [u["unit_code"] for u in all_avail] == ["A-5", "B-1", "A-6"]


async def test_unit_edit_reports_alert_triggers_and_rejects_stale_versions(project):
    unit = await add_unit("A-5", 9_500_000, status="SOLD")
    async with session_scope() as s:
        change = await units.update_unit(s, TENANT, unit["unit_id"], {"status": "AVAILABLE"}, "m1", expected_version=unit["version"])
    assert change.became_available and change.unit["version"] == unit["version"] + 1
    async with session_scope() as s:
        cheaper = await units.update_unit(s, TENANT, unit["unit_id"], {"list_price_bdt": 9_000_000}, "m1")
    assert cheaper.price_dropped and not cheaper.became_available
    with pytest.raises(Conflict):
        async with session_scope() as s:
            await units.update_unit(s, TENANT, unit["unit_id"], {"notes": "x"}, "m1", expected_version=unit["version"])


async def test_concurrent_unit_writes_raise_instead_of_overwriting(project, db):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    unit = await add_unit()
    maker = async_sessionmaker(db, expire_on_commit=False)
    async with maker() as a, maker() as b:
        ua = await a.get(PropertyUnit, unit["unit_id"])
        ub = await b.get(PropertyUnit, unit["unit_id"])
        ua.status = "SOLD"
        await a.commit()
        ub.list_price_bdt = 1
        with pytest.raises(StaleDataError):
            await b.commit()


def test_payment_plan_split_adds_up():
    plan = PaymentPlan(name="36 months", booking_money_bdt=500_000, down_payment_pct=20, installment_months=36)
    result = units.calculate_plan(9_500_000, plan)
    assert result["down_payment_bdt"] == 1_900_000
    total = result["down_payment_bdt"] + result["monthly_installment_bdt"] * 35 + result["last_installment_bdt"]
    assert total == 9_500_000


async def test_expired_holds_go_back_on_sale(project):
    unit = await add_unit()
    async with session_scope() as s:
        row = await s.get(PropertyUnit, unit["unit_id"])
        await units.hold_unit(s, row, "lead-x", 1, "m1")
        row.held_until = now_utc() - timedelta(minutes=1)
    async with session_scope() as s:
        released = await units.release_expired_holds(s)
        row = await s.get(PropertyUnit, unit["unit_id"])
    assert released == [unit["unit_id"]] and row.status == "AVAILABLE"


# ── Leads ─────────────────────────────────────────────────────────────

async def test_lead_identity_is_reused_and_profile_qualifies(db):
    async with session_scope() as s:
        lead, created = await leads.get_or_create_lead(s, TENANT, "whatsapp", "88017", name="Rahim")
        again, created_again = await leads.get_or_create_lead(s, TENANT, "whatsapp", "88017")
        assert created and not created_again and again.lead_id == lead.lead_id
        result = await leads.update_profile(s, lead, {"budget_max_bdt": 10_000_000, "preferred_areas": ["Gulshan", "gulshan "]}, "ai")
    assert result["stage"] == "QUALIFIED"
    assert lead.preferred_areas == ["Gulshan"]  # the same area typed twice is kept once
    assert lead.score == 40


async def test_ai_cannot_move_leads_past_visit_and_lost_needs_reason(db):
    async with session_scope() as s:
        lead, _ = await leads.get_or_create_lead(s, TENANT, "telegram", "42")
        with pytest.raises(SalesError) as err:
            await leads.change_stage(s, lead, "NEGOTIATING", "ai", by_ai=True)
        assert err.value.code == "STAGE_NOT_ALLOWED"
        with pytest.raises(SalesError):
            await leads.change_stage(s, lead, "LOST", "agent-1", by_ai=False)
        await leads.change_stage(s, lead, "LOST", "agent-1", by_ai=False, lost_reason="bought elsewhere")
        assert lead.stage == "LOST" and lead.lost_reason == "bought elsewhere"


async def test_new_leads_go_to_the_least_loaded_agent(db):
    async with session_scope() as s:
        for uid in ("agent-a", "agent-b"):
            s.add(AuthUserRecord(id=uid, email=f"{uid}@x.com", full_name=uid, role="agent", tenant_id=TENANT, hashed_password="x"))
    async with session_scope() as s:
        first, _ = await leads.get_or_create_lead(s, TENANT, "whatsapp", "1")
        second, _ = await leads.get_or_create_lead(s, TENANT, "whatsapp", "2")
        third, _ = await leads.get_or_create_lead(s, TENANT, "whatsapp", "3")
    assert first.owner_user_id == "agent-a" and second.owner_user_id == "agent-b" and third.owner_user_id == "agent-a"


# ── Visits ────────────────────────────────────────────────────────────

async def test_booking_a_free_slot_moves_the_lead_and_respects_capacity(project):
    await add_daily_slots(capacity=1)
    lead_id, _ = await make_lead()
    other_id, _ = await make_lead(external_id="8801711000002", name="Karim")
    async with session_scope() as s:
        slots = await visits.free_slots(s, TENANT, "proj_gulshan")
        assert slots and all(s_["seats_left"] == 1 for s_ in slots)
        lead = await s.get(SalesLead, lead_id)
        from datetime import datetime

        start = datetime.fromisoformat(slots[0]["slot_start"])
        visit, created = await visits.book_visit(s, lead, "proj_gulshan", start, booked_by="ai", idempotency_key="k1")
        assert created and lead.stage == "VISIT_BOOKED"
        repeat, created_again = await visits.book_visit(s, lead, "proj_gulshan", start, booked_by="ai", idempotency_key="k1")
        assert not created_again and repeat["visit_id"] == visit["visit_id"]
        with pytest.raises(Conflict) as dup:
            await visits.book_visit(s, lead, "proj_gulshan", datetime.fromisoformat(slots[1]["slot_start"]), booked_by="ai")
        assert dup.value.code == "VISIT_ALREADY_BOOKED"
        other = await s.get(SalesLead, other_id)
        with pytest.raises(Conflict) as full:
            await visits.book_visit(s, other, "proj_gulshan", start, booked_by="ai")
        assert full.value.code == "SLOT_FULL"
        with pytest.raises(Conflict) as not_offered:
            await visits.book_visit(s, other, "proj_gulshan", start + timedelta(minutes=30), booked_by="ai")
        assert not_offered.value.code == "SLOT_NOT_OFFERED"
        remaining = await visits.free_slots(s, TENANT, "proj_gulshan")
    assert slots[0]["slot_start"] not in [r["slot_start"] for r in remaining]


async def test_reschedule_frees_the_old_slot(project):
    from datetime import datetime

    await add_daily_slots()
    lead_id, _ = await make_lead()
    async with session_scope() as s:
        slots = await visits.free_slots(s, TENANT, "proj_gulshan")
        lead = await s.get(SalesLead, lead_id)
        visit, _ = await visits.book_visit(s, lead, "proj_gulshan", datetime.fromisoformat(slots[0]["slot_start"]), booked_by="ai")
        row = await visits.get_visit(s, TENANT, visit["visit_id"])
        moved = await visits.reschedule_visit(s, row, datetime.fromisoformat(slots[1]["slot_start"]), "ai")
        assert row.status == "CANCELLED" and moved["status"] == "BOOKED"
        free = [x["slot_start"] for x in await visits.free_slots(s, TENANT, "proj_gulshan")]
    assert slots[0]["slot_start"] in free


# ── Approvals ─────────────────────────────────────────────────────────

async def test_unit_hold_needs_a_person_and_is_rechecked(project):
    unit = await add_unit()
    lead_id, _ = await make_lead()
    async with session_scope() as s:
        lead = await s.get(SalesLead, lead_id)
        request = await approvals.request_unit_hold(s, lead, unit["unit_id"], "wants to think 2 days", "ai")
        assert (await s.get(PropertyUnit, unit["unit_id"])).status == "AVAILABLE"
        with pytest.raises(SalesError):
            await approvals.decide(s, TENANT, request["approval_id"], "APPROVED", "ai", None, 48)
        decided = await approvals.decide(s, TENANT, request["approval_id"], "APPROVED", "manager-1", "ok", 48)
        held = await s.get(PropertyUnit, unit["unit_id"])
    assert decided["status"] == "APPROVED" and held.status == "HELD" and held.held_for_lead_id == lead_id


async def test_approval_is_refused_when_the_unit_changed_meanwhile(project):
    unit = await add_unit()
    lead_id, _ = await make_lead()
    async with session_scope() as s:
        lead = await s.get(SalesLead, lead_id)
        request = await approvals.request_unit_hold(s, lead, unit["unit_id"], "", "ai")
    async with session_scope() as s:
        await units.update_unit(s, TENANT, unit["unit_id"], {"status": "SOLD"}, "manager-2")
    with pytest.raises(Conflict) as err:
        async with session_scope() as s:
            await approvals.decide(s, TENANT, request["approval_id"], "APPROVED", "manager-1", None, 48)
    assert err.value.code == "APPROVAL_STALE"


# ── Messaging rules ───────────────────────────────────────────────────

async def test_inbound_duplicates_are_dropped(db):
    _, conv_id = await make_lead()
    async with session_scope() as s:
        conv = await s.get(SalesConversation, conv_id)
        first = await messaging.record_inbound(s, conv, "hello", "wamid.1")
        second = await messaging.record_inbound(s, conv, "hello", "wamid.1")
    assert first is not None and second is None


async def test_24h_window_and_proactive_limit(db, sent):
    _, conv_id = await make_lead()
    async with session_scope() as s:
        conv = await s.get(SalesConversation, conv_id)
        closed = await messaging.send_text(s, conv, "follow up", sender="ai", proactive=True)
        assert closed.status == "skipped" and closed.error == "OUTSIDE_24H_WINDOW"
        templated = await messaging.send_text(s, conv, "follow up", sender="ai", proactive=True, whatsapp_template="glg_followup")
        assert templated.status == "sent" and sent.messages[-1]["template"] == "glg_followup"
        conv.last_customer_message_at = now_utc()
        second = await messaging.send_text(s, conv, "again", sender="ai", proactive=True)
        assert second.status == "skipped" and second.error == "PROACTIVE_LIMIT_48H"
        reply = await messaging.send_text(s, conv, "answer", sender="ai")
        assert reply.status == "sent"


async def test_unconfigured_channels_report_not_sent(db, monkeypatch):
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    _, conv_id = await make_lead()
    async with session_scope() as s:
        conv = await s.get(SalesConversation, conv_id)
        conv.last_customer_message_at = now_utc()
        msg = await messaging.send_text(s, conv, "hi", sender="ai")
    assert msg.status == "not_sent" and msg.error == "WHATSAPP_NOT_CONFIGURED"


async def test_staff_reply_takes_the_chat(db, sent):
    _, conv_id = await make_lead(channel="telegram", external_id="555")
    async with session_scope() as s:
        conv = await s.get(SalesConversation, conv_id)
        await messaging.staff_reply(s, conv, "I'll call you", "agent-7")
    assert conv.mode == "HUMAN" and conv.assigned_user_id == "agent-7"


# ── Inbound path ──────────────────────────────────────────────────────

async def test_inbound_creates_lead_enrolls_and_queues_one_turn(db, jobs_queue):
    async with session_scope() as s:
        await followups.install_default_sequences(s, TENANT)
    msg = InboundMessage(tenant_id=TENANT, channel="whatsapp", external_id="8801711000009", text="flat ache?", channel_message_id="w1", name="Nadia")
    first = await handle_inbound(msg)
    assert first["status"] == "accepted" and first["new_lead"] and first["agent_turn"] == "queued"
    again = await handle_inbound(msg)
    assert again["status"] == "duplicate"
    burst = await handle_inbound(InboundMessage(tenant_id=TENANT, channel="whatsapp", external_id="8801711000009", text="3 bed", channel_message_id="w2"))
    assert burst["agent_turn"] == "already_queued_or_unavailable"
    assert len(queued(jobs_queue, "sales.run_agent_turn")) == 1
    assert len(queued(jobs_queue, "sales.followup_step")) == 1
    async with session_scope() as s:
        lead = (await s.execute(select(SalesLead))).scalar_one()
        enrollments = (await s.execute(select(FollowupEnrollment))).scalars().all()
    assert lead.phone == "8801711000009" and lead.name == "Nadia"
    assert [e.status for e in enrollments] == ["STOPPED"]  # the second message is a reply: nurture pauses


async def test_inbound_does_not_queue_turns_when_off_or_human(db, jobs_queue):
    from sales_fixtures import set_mode

    await set_mode("off")
    result = await handle_inbound(InboundMessage(tenant_id=TENANT, channel="telegram", external_id="9", text="hi"))
    assert result["agent_turn"] == "not_run"
    assert queued(jobs_queue, "sales.run_agent_turn") == []


# ── Follow-ups and workflows ──────────────────────────────────────────

async def test_followup_step_sends_and_schedules_the_next(db, sent, jobs_queue):
    lead_id, conv_id = await make_lead(channel="telegram", external_id="77")
    async with session_scope() as s:
        await followups.install_default_sequences(s, TENANT)
        lead = await s.get(SalesLead, lead_id)
        enrollment = await followups.enroll(s, lead, "new_lead")
        enrollment.next_run_at = now_utc() - timedelta(seconds=1)
        eid = enrollment.enrollment_id
    result = await workflows.run_followup_step(eid)
    assert result["status"] == "sent" and "Rahim" in sent.messages[-1]["text"]
    async with session_scope() as s:
        enrollment = await s.get(FollowupEnrollment, eid)
        lead = await s.get(SalesLead, lead_id)
    assert enrollment.next_position == 1 and enrollment.status == "ACTIVE"
    assert lead.next_followup_at is not None
    assert len(queued(jobs_queue, "sales.followup_step")) == 1
    assert (await workflows.run_followup_step(eid))["status"] == "skipped"  # not due yet


async def test_visit_outcome_check_marks_no_show_and_starts_sequence(project, sent, jobs_queue):
    from datetime import datetime

    await add_daily_slots()
    lead_id, _ = await make_lead(channel="telegram", external_id="88")
    async with session_scope() as s:
        await followups.install_default_sequences(s, TENANT)
        slots = await visits.free_slots(s, TENANT, "proj_gulshan")
        lead = await s.get(SalesLead, lead_id)
        visit, _ = await visits.book_visit(s, lead, "proj_gulshan", datetime.fromisoformat(slots[0]["slot_start"]), booked_by="ai")
        row = await visits.get_visit(s, TENANT, visit["visit_id"])
        row.slot_start = now_utc() - timedelta(hours=3)
        row.slot_end = now_utc() - timedelta(hours=2)
    result = await workflows.check_visit_outcome(visit["visit_id"])
    assert result == {"status": "no_show", "enrolled": True}
    assert len(queued(jobs_queue, "sales.followup_step")) == 1
    assert (await workflows.check_visit_outcome(visit["visit_id"]))["status"] == "skipped"


async def test_unit_match_alert_only_reaches_fitting_leads_once(project, sent):
    unit = await add_unit("A-9", 9_000_000, bedrooms=3)
    fit_id, fit_conv = await make_lead(channel="telegram", external_id="1", name="Fit")
    miss_id, _ = await make_lead(channel="telegram", external_id="2", name="Miss")
    async with session_scope() as s:
        await leads.update_profile(s, await s.get(SalesLead, fit_id), {"budget_max_bdt": 10_000_000, "preferred_areas": ["Gulshan"], "bedrooms": 3}, "agent")
        await leads.update_profile(s, await s.get(SalesLead, miss_id), {"budget_max_bdt": 8_000_000, "preferred_areas": ["Gulshan"]}, "agent")
    first = await workflows.send_unit_match_alerts(TENANT, unit["unit_id"])
    assert first["sent"] == 1 and sent.messages[-1]["to"] == "1" and "৳9,000,000" in sent.messages[-1]["text"]
    second = await workflows.send_unit_match_alerts(TENANT, unit["unit_id"])
    assert second["sent"] == 0


async def test_digest_counts_real_rows(project):
    await make_lead()
    text = await workflows.build_digest(TENANT)
    assert "Pipeline: New 1" in text and "Approvals waiting: 0" in text


async def test_schedule_visit_jobs_queues_reminders(project, jobs_queue):
    visit = {"visit_id": "v1", "slot_start": utc_in(days=2).isoformat(), "slot_end": utc_in(days=2, hours=1).isoformat()}
    queued_ids = await workflows.schedule_visit_jobs(visit)
    assert set(queued_ids) == {"24h", "2h", "outcome"} and all(queued_ids.values())
    assert len(queued(jobs_queue, "sales.visit_reminder")) == 2


async def test_stale_leads_are_reengaged(db, jobs_queue):
    async with session_scope() as s:
        await followups.install_default_sequences(s, TENANT)
        lead, _ = await leads.get_or_create_lead(s, TENANT, "telegram", "quiet")
        lead.last_contact_at = now_utc() - timedelta(days=6)
    result = await workflows.sweep_stale_leads()
    assert result["reengaged"] == 1
    assert (await workflows.sweep_stale_leads())["reengaged"] == 0

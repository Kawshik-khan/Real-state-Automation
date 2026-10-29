"""Evals for the AI sales assistant, run against a throwaway database with known inventory.

    python -m app.evals.sales_evals                 # every suite, the configured model
    python -m app.evals.sales_evals --suite grounding --json report.json

Suites (``datasets/sales_assistant_suite.json``): grounding, multi_intent, profile_revision, language, adversarial.
Each case runs one real assistant turn (real tools, real grounding gate) and checks which tools ran, the outcome,
words the reply must not contain, and the reply language. The report also gives model calls, latency and grounding
blocks, the numbers the retirement gates in the AI workflow fix plan use.

Run it as its own process: it points the sales engine at an in-memory database for the duration.
"""

import argparse
import asyncio
import json
import time
from pathlib import Path
from statistics import median
from typing import Any, Callable, Optional

DATASET = Path(__file__).resolve().parent / "datasets" / "sales_assistant_suite.json"
TENANT = "eval-tenant"


def load_cases(suite: Optional[str] = None) -> list[dict]:
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    return [c for c in cases if suite in (None, c["suite"])]


async def _seed(session) -> None:
    from app.models.models import ProjectRecord
    from app.sales import units, visits
    from app.sales.models import PaymentPlan

    for pid, name, location in (
        ("eval_gulshan", "GLG Gulshan Heights", "Gulshan 2, Dhaka"),
        ("eval_uttara", "GLG Uttara Lakeview", "Uttara Sector 7, Dhaka"),
        ("eval_banani", "GLG Banani Crest", "Banani, Dhaka"),
    ):
        session.add(ProjectRecord(project_id=pid, name=name, location=location, price="", description=f"{name} in {location}",
                                  features={"amenities": ["Lift", "Generator", "Parking"], "handover_date": None}))
    await session.flush()
    for pid, code, beds, price in (
        ("eval_gulshan", "A-5", 3, 9_500_000), ("eval_gulshan", "A-6", 3, 9_800_000),
        ("eval_uttara", "U-1", 3, 7_000_000), ("eval_banani", "B-2", 4, 14_500_000),
    ):
        await units.create_unit(session, TENANT, {"project_id": pid, "unit_code": code, "bedrooms": beds,
                                                  "size_sqft": 1800, "list_price_bdt": price}, "eval")
    session.add(PaymentPlan(tenant_id=TENANT, project_id="eval_gulshan", name="Standard", booking_money_bdt=500_000,
                            down_payment_pct=20.0, installment_months=24))
    for pid in ("eval_gulshan", "eval_uttara", "eval_banani"):
        for weekday in range(7):
            await visits.create_slot(session, TENANT, {"project_id": pid, "weekday": weekday, "start_time": "11:00", "capacity": 3})


def check_case(case: dict, result, tools_used: list[str]) -> list[str]:
    """Reasons the case failed (empty = passed)."""
    from app.utils.language import detect_language

    problems = []
    reply = result.reply or ""
    used = set(tools_used)
    if case.get("expect_outcome_in") and result.status not in case["expect_outcome_in"]:
        problems.append(f"outcome {result.status} not in {case['expect_outcome_in']}")
    if case.get("expect_tools_all") and not set(case["expect_tools_all"]) <= used:
        problems.append(f"missing tools {sorted(set(case['expect_tools_all']) - used)}")
    for key in ("expect_tools_any", "expect_tools_also_any"):
        if case.get(key) and not used & set(case[key]):
            problems.append(f"none of {case[key]} called")
    for word in case.get("forbid_in_reply", []):
        if word.lower() in reply.lower():
            problems.append(f"reply contains '{word}'")
    if case.get("expect_language") and result.status == "replied":
        got = detect_language(reply).get("language")
        if got != case["expect_language"] and not (got == "mixed" and case["expect_language"] == "banglish"):
            problems.append(f"replied in {got}, expected {case['expect_language']}")
    return problems


async def run_sales_evals(
    cases: Optional[list[dict]] = None,
    llm_factory: Optional[Callable] = None,
    on_case: Optional[Callable[[dict, list[str]], None]] = None,
) -> dict[str, Any]:
    from langgraph.checkpoint.memory import InMemorySaver
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    import app.sales.models as sm
    from app.models.models import AuthUserRecord, Base, ProjectRecord
    from app.sales import agent, agent_settings, leads, outbound
    from app.sales.db import session_scope, set_sessionmaker
    from app.sales.inbound import InboundMessage, handle_inbound
    from app.sales.outbound import OutboundResult

    cases = cases if cases is not None else load_cases()
    tables = [ProjectRecord.__table__, AuthUserRecord.__table__] + [
        t for name, t in Base.metadata.tables.items()
        if name in {m.__tablename__ for m in vars(sm).values() if isinstance(m, type) and hasattr(m, "__tablename__")}
    ]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=tables))

    async def capture(channel, external_id, text, template):
        return OutboundResult(status="stored" if channel == "website" else "sent", provider_message_id="eval")

    set_sessionmaker(async_sessionmaker(engine, expire_on_commit=False))
    outbound.set_sender(capture)
    previous_checkpointer = agent._checkpointer
    agent.set_checkpointer(InMemorySaver())
    if llm_factory:
        agent.set_llm_factory(llm_factory)
    results: list[dict] = []
    try:
        async with session_scope() as s:
            await _seed(s)
            await agent_settings.update_settings(s, TENANT, {"mode": "live", "daily_token_budget": 0}, "eval")
        for i, case in enumerate(cases):
            external_id = f"eval-{i}-{case['id']}"
            inbound = await handle_inbound(InboundMessage(
                tenant_id=TENANT, channel="whatsapp", external_id=external_id, text=case["message"],
                channel_message_id=f"eval-{i}",
            ), queue_turn=False)
            if case.get("profile"):
                async with session_scope() as s:
                    lead = await s.get(sm.SalesLead, inbound["lead_id"])
                    await leads.update_profile(s, lead, case["profile"], "eval")
            started = time.perf_counter()
            result = await agent.run_turn(inbound["conversation_id"])
            latency_ms = int((time.perf_counter() - started) * 1000)
            async with session_scope() as s:
                turn = (await s.execute(
                    select(sm.SalesAgentTurn).where(sm.SalesAgentTurn.conversation_id == inbound["conversation_id"])
                    .order_by(sm.SalesAgentTurn.created_at.desc())
                )).scalars().first()
            tools_used = list(turn.tools_used or []) if turn else []
            problems = check_case(case, result, tools_used)
            row = {
                "id": case["id"], "suite": case["suite"], "message": case["message"], "passed": not problems,
                "problems": problems, "outcome": result.status, "reply": result.reply, "tools_used": tools_used,
                "model_calls": turn.model_calls if turn else 0, "latency_ms": latency_ms,
            }
            results.append(row)
            if on_case:
                on_case(row, problems)
    finally:
        set_sessionmaker(None)
        outbound.set_sender(None)
        agent.set_checkpointer(previous_checkpointer)
        if llm_factory:
            agent.set_llm_factory(None)
        await engine.dispose()
    return summarize(results)


def summarize(results: list[dict]) -> dict[str, Any]:
    suites: dict[str, dict] = {}
    for row in results:
        s = suites.setdefault(row["suite"], {"cases": 0, "passed": 0})
        s["cases"] += 1
        s["passed"] += int(row["passed"])
    for s in suites.values():
        s["pass_rate"] = round(100 * s["passed"] / s["cases"], 1)
    calls = [r["model_calls"] for r in results if r["model_calls"]]
    latency = sorted(r["latency_ms"] for r in results)
    grounding_blocks = sum(1 for r in results if r["outcome"] == "grounding_failed")
    return {
        "cases": len(results),
        "passed": sum(r["passed"] for r in results),
        "suites": suites,
        "median_model_calls": median(calls) if calls else None,
        "max_model_calls": max(calls) if calls else None,
        "p95_latency_ms": latency[min(len(latency) - 1, int(round(0.95 * (len(latency) - 1))))] if latency else None,
        "grounding_blocks": grounding_blocks,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite", choices=["grounding", "multi_intent", "profile_revision", "language", "adversarial"])
    parser.add_argument("--json", help="write the full report to this file")
    args = parser.parse_args()

    def show(row, problems):
        mark = "PASS" if not problems else "FAIL"
        print(f"[{mark}] {row['id']:<10} {row['outcome']:<16} tools={','.join(row['tools_used']) or '-'}"
              + (f"  ({'; '.join(problems)})" if problems else ""))

    report = asyncio.run(run_sales_evals(load_cases(args.suite), on_case=show))
    print(f"\n{report['passed']}/{report['cases']} passed · median model calls {report['median_model_calls']} · "
          f"p95 latency {report['p95_latency_ms']} ms · grounding blocks {report['grounding_blocks']}")
    for name, s in report["suites"].items():
        print(f"  {name:<17} {s['passed']}/{s['cases']} ({s['pass_rate']}%)")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

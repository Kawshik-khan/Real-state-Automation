"""Shared fixtures for the sales engine tests: a SQLite database per test, a fake channel sender, an in-memory job
queue and a scripted LLM. No network, no Postgres needed."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from procrastinate.testing import InMemoryConnector
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models.models import AuthUserRecord, Base, ProjectRecord
from app.sales import agent, outbound
from app.sales import models as sm
from app.sales.db import session_scope, set_sessionmaker
from app.sales.jobs import queue
from app.sales.outbound import OutboundResult

TENANT = "glg-test"

SALES_TABLES = [
    ProjectRecord.__table__, AuthUserRecord.__table__, sm.PropertyUnit.__table__, sm.PaymentPlan.__table__,
    sm.SalesLead.__table__, sm.LeadEvent.__table__, sm.VisitSlot.__table__, sm.SiteVisit.__table__,
    sm.FollowupSequence.__table__, sm.FollowupStep.__table__, sm.FollowupEnrollment.__table__,
    sm.SalesConversation.__table__, sm.SalesMessage.__table__, sm.SalesApproval.__table__,
    sm.SalesAgentSettings.__table__, sm.SalesAgentTurn.__table__, sm.AIShadowPair.__table__,
]


@dataclass
class SentLog:
    messages: list = field(default_factory=list)
    fail_channels: set = field(default_factory=set)

    async def __call__(self, channel, external_id, text, template):
        if channel in self.fail_channels:
            return OutboundResult(status="not_sent", error="TEST_FAILURE")
        self.messages.append({"channel": channel, "to": external_id, "text": text, "template": template})
        return OutboundResult(status="stored" if channel == "website" else "sent", provider_message_id=f"p{len(self.messages)}")


@pytest_asyncio.fixture
async def db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/sales.db", poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=SALES_TABLES))
    set_sessionmaker(async_sessionmaker(engine, expire_on_commit=False))
    yield engine
    set_sessionmaker(None)
    await engine.dispose()


@pytest.fixture
def sent():
    log = SentLog()
    outbound.set_sender(log)
    yield log
    outbound.set_sender(None)


@pytest_asyncio.fixture
async def jobs_queue():
    connector = InMemoryConnector()
    with queue.replace_connector(connector):
        async with queue.open_async():
            yield connector


def queued(connector: InMemoryConnector, task_name: str) -> list[dict]:
    return [j for j in connector.jobs.values() if j["task_name"] == task_name and j["status"] == "todo"]


@pytest_asyncio.fixture
async def project(db):
    async with session_scope() as s:
        s.add(ProjectRecord(project_id="proj_gulshan", name="GLG Gulshan Heights", location="Gulshan 2, Dhaka", price="95 Lakh", description=""))
        s.add(ProjectRecord(project_id="proj_banani", name="GLG Banani Crest", location="Banani, Dhaka", price="1.2 Crore", description=""))
    return "proj_gulshan"


async def add_unit(code="A-5", price=9_500_000, status="AVAILABLE", project_id="proj_gulshan", bedrooms=3, **extra):
    from app.sales import units

    async with session_scope() as s:
        return await units.create_unit(
            s, TENANT, {"project_id": project_id, "unit_code": code, "list_price_bdt": price, "status": status, "bedrooms": bedrooms, "size_sqft": 1850, **extra}, "manager-1"
        )


async def add_daily_slots(project_id="proj_gulshan", start_time="11:00", capacity=1, tenant=TENANT):
    from app.sales import visits

    async with session_scope() as s:
        for weekday in range(7):
            await visits.create_slot(s, tenant, {"project_id": project_id, "weekday": weekday, "start_time": start_time, "capacity": capacity})


async def make_lead(channel="whatsapp", external_id="8801711000001", name="Rahim"):
    from app.sales import leads, messaging

    async with session_scope() as s:
        lead, _ = await leads.get_or_create_lead(s, TENANT, channel, external_id, name=name)
        conv = await messaging.get_or_create_conversation(s, lead)
        return lead.lead_id, conv.conversation_id


async def set_mode(mode: str, **fields):
    from app.sales import agent_settings

    async with session_scope() as s:
        await agent_settings.update_settings(s, TENANT, {"mode": mode, **fields}, "manager-1")


def utc_in(**delta) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**delta)


# ── Scripted LLM ──────────────────────────────────────────────────────

def tool_call(name: str, args: dict, call_id: str = "c1") -> agent.ToolCall:
    return agent.ToolCall(id=call_id, name=name, arguments=json.dumps(args))


class ScriptedLLM:
    """Plays back responses. A step may be an LLMResponse or a function(messages) -> LLMResponse."""

    def __init__(self, steps):
        self.steps = list(steps)
        self.calls: list[list[dict]] = []

    async def complete(self, messages, tools):
        self.calls.append({"messages": list(messages), "tools": [t["function"]["name"] for t in tools]})
        step = self.steps.pop(0) if self.steps else agent.LLMResponse(content="")
        return step(messages) if callable(step) else step


@pytest.fixture
def llm():
    holder = {}

    def install(steps):
        scripted = ScriptedLLM(steps)
        holder["llm"] = scripted
        agent.set_llm_factory(lambda: scripted)
        return scripted

    yield install
    agent.set_llm_factory(None)

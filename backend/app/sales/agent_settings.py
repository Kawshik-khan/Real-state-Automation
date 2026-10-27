"""Per-tenant switches for the AI sales assistant: off / shadow / live, channels, kill switch, budget."""

from datetime import datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales.db import DHAKA, now_utc
from app.sales.errors import SalesError
from app.sales.leads import iso
from app.sales.models import CHANNELS, SalesAgentSettings, SalesAgentTurn

MODES = ("off", "shadow", "live")


def settings_to_dict(s: SalesAgentSettings) -> dict:
    return {
        "mode": s.mode,
        "enabled_channels": s.enabled_channels or [],
        "kill_switch": s.kill_switch,
        "daily_token_budget": s.daily_token_budget,
        "hold_hours": s.hold_hours,
        "digest_chat_id": s.digest_chat_id,
        "updated_by": s.updated_by,
        "updated_at": iso(s.updated_at),
    }


async def get_settings(session: AsyncSession, tenant_id: str) -> SalesAgentSettings:
    row = await session.get(SalesAgentSettings, tenant_id)
    if row is None:
        # New tenants start in shadow mode: the assistant drafts, nobody is messaged until a manager turns it live.
        row = SalesAgentSettings(tenant_id=tenant_id, mode="shadow", enabled_channels=list(CHANNELS))
        session.add(row)
        await session.flush()
    return row


async def update_settings(session: AsyncSession, tenant_id: str, fields: dict, actor: str) -> dict:
    row = await get_settings(session, tenant_id)
    if "mode" in fields:
        if fields["mode"] not in MODES:
            raise SalesError("INVALID_MODE", f"Mode must be one of {', '.join(MODES)}")
        row.mode = fields["mode"]
    if "enabled_channels" in fields:
        bad = [c for c in fields["enabled_channels"] if c not in CHANNELS]
        if bad:
            raise SalesError("INVALID_CHANNEL", f"Unknown channels: {', '.join(bad)}")
        row.enabled_channels = list(fields["enabled_channels"])
    if "kill_switch" in fields:
        row.kill_switch = bool(fields["kill_switch"])
    if "daily_token_budget" in fields:
        if int(fields["daily_token_budget"]) < 0:
            raise SalesError("INVALID_BUDGET", "Budget must be 0 or more tokens")
        row.daily_token_budget = int(fields["daily_token_budget"])
    if "hold_hours" in fields:
        if not 1 <= int(fields["hold_hours"]) <= 168:
            raise SalesError("INVALID_HOLD", "Hold time must be 1–168 hours")
        row.hold_hours = int(fields["hold_hours"])
    if "digest_chat_id" in fields:
        row.digest_chat_id = fields["digest_chat_id"] or None
    row.updated_by = actor
    row.updated_at = now_utc()
    await session.flush()
    return settings_to_dict(row)


def start_of_today_utc() -> datetime:
    local_midnight = datetime.combine(now_utc().astimezone(DHAKA).date(), time(0), tzinfo=DHAKA)
    return local_midnight.astimezone(timezone.utc)


async def tokens_used_today(session: AsyncSession, tenant_id: str) -> int:
    return await session.scalar(
        select(func.coalesce(func.sum(SalesAgentTurn.tokens), 0)).where(
            SalesAgentTurn.tenant_id == tenant_id, SalesAgentTurn.created_at >= start_of_today_utc()
        )
    ) or 0


async def turns_since(session: AsyncSession, conversation_id: str, since: datetime) -> int:
    return await session.scalar(
        select(func.count()).select_from(SalesAgentTurn).where(
            SalesAgentTurn.conversation_id == conversation_id, SalesAgentTurn.created_at >= since
        )
    ) or 0

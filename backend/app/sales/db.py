"""Session access and time helpers for the sales engine.

Services take an ``AsyncSession``; jobs, tools and webhooks open their own through ``session_scope()``. Tests point
the engine at another database with ``set_sessionmaker()``.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

DHAKA = ZoneInfo("Asia/Dhaka")

_sessionmaker: Optional[async_sessionmaker] = None


def set_sessionmaker(factory: Optional[async_sessionmaker]) -> None:
    global _sessionmaker
    _sessionmaker = factory


def get_sessionmaker() -> async_sessionmaker:
    if _sessionmaker is not None:
        return _sessionmaker
    from app.database import async_session_factory

    return async_session_factory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """A session that commits on success and rolls back on error."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_sales_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, committed by the handler's service calls."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Databases without timezone support (SQLite) return naive datetimes; treat those as UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_dhaka(value: datetime) -> datetime:
    return as_utc(value).astimezone(DHAKA)


def format_dhaka(value: datetime) -> str:
    """Human-readable local time, e.g. 'Sat 1 Nov 2026, 3:00 PM'."""
    local = to_dhaka(value)
    return local.strftime("%a %-d %b %Y, %-I:%M %p")

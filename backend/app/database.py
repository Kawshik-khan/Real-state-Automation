"""Async SQLAlchemy engine for the GLG Assets backend.

Provides async engine, session factory, connection checks, and Supabase init_db.
Import get_session as a FastAPI dependency in route handlers.
"""
import socket
import time
from typing import AsyncGenerator
from urllib.parse import urlparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.models import Base

# Enhanced engine parameters for Supabase Transaction Pooler (Port 6543 / 5432)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=300,
    pool_pre_ping=True,
    connect_args={"timeout": 3, "command_timeout": 5} if "postgresql" in settings.database_url else {}
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()



_db_status = {"reachable": None, "checked_at": 0}

def is_db_reachable(timeout: float = 0.3) -> bool:
    """Fast non-blocking socket pre-flight check to verify if the DB port is open."""
    now = time.time()
    if now - _db_status["checked_at"] < 15.0 and _db_status["reachable"] is not None:
        return _db_status["reachable"]
    try:
        clean = settings.database_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://")
        p = urlparse(clean)
        host = p.hostname or "localhost"
        port = p.port or 5432
        with socket.create_connection((host, port), timeout=timeout):
            _db_status["reachable"] = True
            _db_status["checked_at"] = now
            return True
    except Exception:
        _db_status["reachable"] = False
        _db_status["checked_at"] = now
        return False


async def check_connection() -> bool:
    """Verify the database is reachable. Returns True if connected."""
    if not is_db_reachable():
        return False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def init_db():
    """Initialize database tables and enable pgvector & uuid-ossp extensions on Supabase/PostgreSQL."""
    # Ensure all AI Control Plane models are registered in Base.metadata
    import app.models.ai_control_plane  # noqa: F401

    async with engine.begin() as conn:
        # Enable pgvector & UUID extensions natively
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
        except Exception:
            pass
        
        # Create all tables defined in Base.metadata
        await conn.run_sync(Base.metadata.create_all)


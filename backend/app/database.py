"""Async SQLAlchemy engine for the GLG Assets backend.

Provides async engine, session factory, connection checks, and Supabase init_db.
Import get_session as a FastAPI dependency in route handlers.
"""
from typing import AsyncGenerator
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


async def check_connection() -> bool:
    """Verify the database is reachable. Returns True if connected."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def init_db():
    """Initialize database tables and enable pgvector & uuid-ossp extensions on Supabase/PostgreSQL."""
    async with engine.begin() as conn:
        # Enable pgvector & UUID extensions natively
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
        except Exception:
            pass
        
        # Create all 9 tables defined in Base.metadata
        await conn.run_sync(Base.metadata.create_all)

"""Database-backed User Service with Bcrypt Hashing and In-Memory Resilient Fallback.

Solves [S-03]: In-Memory User Database with Hardcoded Passwords.
Migrates staff users to the PostgreSQL `auth_users` table with bcrypt 12-round hashes.
Maintains a synchronized in-memory fallback for local offline testing and high availability.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password
from app.database import async_session_factory
from app.models.models import AuthUserRecord
from app.models.user import UserCreate, UserInDB, UserResponse, UserRole

logger = logging.getLogger(__name__)

DEFAULT_SEED_USERS = [
    {
        "id": "usr-admin-001",
        "email": "admin@glgassets.com",
        "full_name": "Alex Mercer (Admin)",
        "role": UserRole.ADMIN,
        "tenant_id": "glg-default",
        "is_active": True,
        "password": "admin123",
    },
    {
        "id": "usr-manager-002",
        "email": "manager@glgassets.com",
        "full_name": "Sarah Connor (Manager)",
        "role": UserRole.MANAGER,
        "tenant_id": "glg-default",
        "is_active": True,
        "password": "manager123",
    },
    {
        "id": "usr-agent-003",
        "email": "agent@glgassets.com",
        "full_name": "Rahul Sharma (Agent)",
        "role": UserRole.AGENT,
        "tenant_id": "glg-default",
        "is_active": True,
        "password": "agent123",
    },
    {
        "id": "usr-dev-005",
        "email": "developer@glgassets.com",
        "full_name": "Alex Chen (Dev Lead)",
        "role": UserRole.DEVELOPER,
        "tenant_id": "glg-default",
        "is_active": True,
        "password": "dev123",
    },
    {
        "id": "usr-viewer-004",
        "email": "viewer@glgassets.com",
        "full_name": "Guest Stakeholder (Viewer)",
        "role": UserRole.VIEWER,
        "tenant_id": "glg-default",
        "is_active": True,
        "password": "viewer123",
    },
]


class UserService:
    """Manages persistent staff authentication records and RBAC."""

    def __init__(self):
        self._in_memory: Dict[str, UserInDB] = {}
        self._lock = asyncio.Lock()
        self._has_seeded = False
        # Demo accounts have publicly known passwords: only create them when explicitly enabled
        # (development / tests). Otherwise the in-memory fallback starts empty.
        if settings.seed_demo_users:
            self._init_in_memory_defaults()

    def _init_in_memory_defaults(self):
        """Pre-populate in-memory cache with hashed seed users for zero-delay offline fallback."""
        now_iso = datetime.now(timezone.utc).isoformat()
        for u in DEFAULT_SEED_USERS:
            email = u["email"].lower()
            self._in_memory[email] = UserInDB(
                id=u["id"],
                email=email,
                full_name=u["full_name"],
                role=u["role"],
                tenant_id=u["tenant_id"],
                is_active=u["is_active"],
                hashed_password=hash_password(u["password"]),
                created_at=now_iso,
            )

    @property
    def in_memory_users(self) -> Dict[str, UserInDB]:
        """Direct access to in-memory users dictionary for legacy USERS_DB compatibility."""
        return self._in_memory

    async def seed_default_users(self) -> None:
        """Seed default staff accounts into PostgreSQL `auth_users` table on startup.

        Only when SEED_DEMO_USERS=true — the demo passwords are public.
        """
        if self._has_seeded or not settings.seed_demo_users:
            return

        try:
            async with async_session_factory() as session:
                for u in DEFAULT_SEED_USERS:
                    email = u["email"].lower()
                    stmt = select(AuthUserRecord).where(AuthUserRecord.email == email)
                    res = await session.execute(stmt)
                    existing = res.scalars().first()

                    if not existing:
                        # Hash password with bcrypt at rest
                        hashed = hash_password(u["password"])
                        rec = AuthUserRecord(
                            id=u["id"],
                            email=email,
                            full_name=u["full_name"],
                            role=u["role"].value if isinstance(u["role"], UserRole) else str(u["role"]),
                            tenant_id=u["tenant_id"],
                            is_active=u["is_active"],
                            hashed_password=hashed,
                        )
                        session.add(rec)

                await session.commit()
                self._has_seeded = True
                logger.info("[UserService] Successfully seeded staff accounts in PostgreSQL `auth_users`.")
        except Exception as err:
            logger.warning(
                f"[UserService] Database seeding skipped (running with in-memory resilient users): {err}"
            )

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Fetch user by email from PostgreSQL, falling back to in-memory store."""
        if not email:
            return None
        email_clean = email.strip().lower()

        # 1. Try PostgreSQL
        try:
            async with async_session_factory() as session:
                stmt = select(AuthUserRecord).where(AuthUserRecord.email == email_clean)
                res = await session.execute(stmt)
                rec = res.scalars().first()
                if rec:
                    user_obj = UserInDB(
                        id=rec.id,
                        email=rec.email,
                        full_name=rec.full_name,
                        role=UserRole(rec.role) if rec.role in [r.value for r in UserRole] else UserRole.AGENT,
                        tenant_id=rec.tenant_id,
                        is_active=rec.is_active,
                        hashed_password=rec.hashed_password,
                        created_at=rec.created_at.isoformat() if rec.created_at else datetime.now(timezone.utc).isoformat(),
                    )
                    # Sync to L1
                    async with self._lock:
                        self._in_memory[email_clean] = user_obj
                    return user_obj
        except Exception as err:
            logger.debug(f"[UserService] Database lookup for '{email_clean}' failed; using in-memory: {err}")

        # 2. In-memory fallback
        async with self._lock:
            return self._in_memory.get(email_clean)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Fetch user by primary ID."""
        if not user_id:
            return None

        # 1. Try PostgreSQL
        try:
            async with async_session_factory() as session:
                stmt = select(AuthUserRecord).where(AuthUserRecord.id == user_id)
                res = await session.execute(stmt)
                rec = res.scalars().first()
                if rec:
                    return UserInDB(
                        id=rec.id,
                        email=rec.email,
                        full_name=rec.full_name,
                        role=UserRole(rec.role) if rec.role in [r.value for r in UserRole] else UserRole.AGENT,
                        tenant_id=rec.tenant_id,
                        is_active=rec.is_active,
                        hashed_password=rec.hashed_password,
                        created_at=rec.created_at.isoformat() if rec.created_at else datetime.now(timezone.utc).isoformat(),
                    )
        except Exception as err:
            logger.debug(f"[UserService] Database lookup for ID '{user_id}' failed: {err}")

        # 2. In-memory fallback
        async with self._lock:
            for u in self._in_memory.values():
                if u.id == user_id:
                    return u
        return None

    async def list_all_users(self) -> List[UserResponse]:
        """List all registered users from database or cache."""
        # 1. Try PostgreSQL
        try:
            async with async_session_factory() as session:
                stmt = select(AuthUserRecord).order_by(AuthUserRecord.created_at)
                res = await session.execute(stmt)
                records = res.scalars().all()
                if records:
                    results = []
                    async with self._lock:
                        for r in records:
                            role_val = UserRole(r.role) if r.role in [ro.value for ro in UserRole] else UserRole.AGENT
                            created_iso = r.created_at.isoformat() if r.created_at else datetime.now(timezone.utc).isoformat()
                            user_db = UserInDB(
                                id=r.id,
                                email=r.email,
                                full_name=r.full_name,
                                role=role_val,
                                tenant_id=r.tenant_id,
                                is_active=r.is_active,
                                hashed_password=r.hashed_password,
                                created_at=created_iso,
                            )
                            self._in_memory[r.email.lower()] = user_db
                            results.append(
                                UserResponse(
                                    id=r.id,
                                    email=r.email,
                                    full_name=r.full_name,
                                    role=role_val,
                                    tenant_id=r.tenant_id,
                                    is_active=r.is_active,
                                    created_at=created_iso,
                                )
                            )
                    return results
        except Exception as err:
            logger.debug(f"[UserService] Database list_all_users failed; using in-memory: {err}")

        # 2. In-memory fallback
        async with self._lock:
            return [
                UserResponse(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
                    role=u.role,
                    tenant_id=u.tenant_id,
                    is_active=u.is_active,
                    created_at=u.created_at,
                )
                for u in self._in_memory.values()
            ]

    async def create_user(self, new_user: UserCreate) -> UserResponse:
        """Create and persist a new user in PostgreSQL and memory."""
        email_clean = new_user.email.strip().lower()

        # Check existence
        existing = await self.get_user_by_email(email_clean)
        if existing:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="User with this email already exists")

        # Generate unique user ID
        usr_id = f"usr-{int(time.time() * 1000) % 1000000:06d}"
        hashed = hash_password(new_user.password)
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        role_val = new_user.role.value if isinstance(new_user.role, UserRole) else str(new_user.role)

        # 1. Persist to PostgreSQL
        try:
            async with async_session_factory() as session:
                rec = AuthUserRecord(
                    id=usr_id,
                    email=email_clean,
                    full_name=new_user.full_name,
                    role=role_val,
                    tenant_id=new_user.tenant_id,
                    is_active=new_user.is_active,
                    hashed_password=hashed,
                    created_at=now_dt,
                )
                session.add(rec)
                await session.commit()
                logger.info(f"[UserService] Registered new user '{email_clean}' in database (ID: {usr_id}).")
        except Exception as err:
            logger.warning(f"[UserService] Failed to write new user to DB (saving to in-memory): {err}")

        # 2. Sync to in-memory
        user_db = UserInDB(
            id=usr_id,
            email=email_clean,
            full_name=new_user.full_name,
            role=new_user.role,
            tenant_id=new_user.tenant_id,
            is_active=new_user.is_active,
            hashed_password=hashed,
            created_at=now_iso,
        )
        async with self._lock:
            self._in_memory[email_clean] = user_db

        return UserResponse(
            id=usr_id,
            email=email_clean,
            full_name=new_user.full_name,
            role=new_user.role,
            tenant_id=new_user.tenant_id,
            is_active=new_user.is_active,
            created_at=now_iso,
        )


# Global user service singleton
user_service = UserService()

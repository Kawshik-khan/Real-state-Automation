"""Database-backed User Service with Bcrypt Hashing and In-Memory Resilient Fallback.

Staff users live in the PostgreSQL `auth_users` table with bcrypt 12-round hashes.
No accounts are hardcoded: the first admin is created from BOOTSTRAP_ADMIN_EMAIL /
BOOTSTRAP_ADMIN_PASSWORD. The in-memory cache is only consulted when the database is unreachable.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select

from app.core.security import hash_password
from app.database import async_session_factory
from app.models.models import AuthUserRecord
from app.models.user import UserCreate, UserInDB, UserResponse, UserRole

logger = logging.getLogger(__name__)


class UserService:
    """Manages persistent staff authentication records and RBAC."""

    def __init__(self):
        # Cache of users loaded from PostgreSQL, plus users registered while the database was unreachable.
        self._in_memory: Dict[str, UserInDB] = {}
        self._lock = asyncio.Lock()
        self._has_bootstrapped = False

    @property
    def in_memory_users(self) -> Dict[str, UserInDB]:
        """Direct access to in-memory users dictionary for legacy USERS_DB compatibility."""
        return self._in_memory

    def cache_user(
        self,
        email: str,
        full_name: str,
        role: UserRole,
        password: str,
        user_id: Optional[str] = None,
        tenant_id: str = "glg-default",
        is_active: bool = True,
    ) -> UserInDB:
        """Register a user in the in-process cache only (tests and offline development)."""
        email_clean = email.strip().lower()
        user_obj = UserInDB(
            id=user_id or f"usr-{int(time.time() * 1000) % 1000000:06d}",
            email=email_clean,
            full_name=full_name,
            role=role,
            tenant_id=tenant_id,
            is_active=is_active,
            hashed_password=hash_password(password),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._in_memory[email_clean] = user_obj
        return user_obj

    async def bootstrap_admin(self) -> None:
        """Create the first admin from BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD if it does not exist yet."""
        from app.config import settings

        if self._has_bootstrapped or not (settings.bootstrap_admin_email and settings.bootstrap_admin_password):
            return

        email = settings.bootstrap_admin_email.strip().lower()
        try:
            async with async_session_factory() as session:
                res = await session.execute(select(AuthUserRecord).where(AuthUserRecord.email == email))
                if not res.scalars().first():
                    session.add(AuthUserRecord(
                        id=f"usr-admin-{int(time.time() * 1000) % 1000000:06d}",
                        email=email,
                        full_name="Administrator",
                        role=UserRole.ADMIN.value,
                        tenant_id=settings.default_tenant_id,
                        is_active=True,
                        hashed_password=hash_password(settings.bootstrap_admin_password),
                    ))
                    await session.commit()
                    logger.info(f"[UserService] Bootstrapped admin account '{email}' in PostgreSQL `auth_users`.")
                self._has_bootstrapped = True
        except Exception as err:
            logger.warning(f"[UserService] Admin bootstrap skipped (database unavailable): {err}")

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Fetch user by email from PostgreSQL, using the in-memory cache only when the database is unreachable."""
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
            # The database answered and has no such user: never resurrect it from the cache.
            async with self._lock:
                self._in_memory.pop(email_clean, None)
            return None
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
            return None
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
                results = []
                if records:
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

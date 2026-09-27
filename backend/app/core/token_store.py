"""Distributed Token Revocation and Session Store (Layered: Memory -> Redis -> PostgreSQL).

Solves [S-07]: In-Memory Token Revocation & Multi-Worker Desynchronization.
Architecture:
- L1 (Fast): In-memory lock-protected cache for local process speed (<0.1ms).
- L2 (Distributed): Redis cache with TTL via resilient_store (<2ms) across all worker instances.
- L3 (Persistent): PostgreSQL tables `active_refresh_tokens` and `revoked_tokens` for durable cross-worker state and reboot resilience.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import delete, select

from app.core.redis_client import resilient_store
from app.database import async_session_factory
from app.models.models import ActiveRefreshTokenRecord, RevokedTokenRecord

logger = logging.getLogger(__name__)


def _utc_from_timestamp(ts: float) -> datetime:
    """Convert POSIX timestamp to timezone-aware UTC datetime."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


class DistributedTokenStore:
    """Distributed token and session store supporting Redis and PostgreSQL."""

    def __init__(self):
        # L1 In-Memory process cache
        self._active_local: Dict[str, Dict[str, Any]] = {}
        self._revoked_local: set = set()
        self._user_revoked_at_local: Dict[str, float] = {}
        self._revoked_sessions_local: set = set()
        self._lock = asyncio.Lock()

    async def record_active_token(
        self,
        jti: str,
        user_id: str,
        role: str,
        email: str,
        expires_at: float,
    ) -> None:
        """Register newly created active refresh token across all layers."""
        now = time.time()
        ttl_seconds = max(1, int(expires_at - now))
        token_info = {
            "sub": user_id,
            "role": role,
            "email": email or "",
            "expires_at": expires_at,
        }

        # 1. L1 Local Memory
        async with self._lock:
            self._active_local[jti] = token_info

        # 2. L2 Redis (TTL-bounded)
        try:
            redis_key = f"token:active:{jti}"
            await resilient_store.set(redis_key, json.dumps(token_info), expire_seconds=ttl_seconds)
        except Exception as err:
            logger.debug(f"[TokenStore] Redis set active token failed: {err}")

        # 3. L3 PostgreSQL persistence
        try:
            async with async_session_factory() as session:
                record = ActiveRefreshTokenRecord(
                    jti=jti,
                    user_id=user_id,
                    role=role,
                    email=email or "",
                    expires_at=_utc_from_timestamp(expires_at),
                )
                session.add(record)
                await session.commit()
        except Exception as err:
            logger.warning(
                f"[TokenStore] Database persist active token '{jti}' failed (using L1/L2): {err}"
            )

    async def is_token_revoked(
        self, jti: str, user_id: Optional[str] = None, issued_at: Optional[float] = None
    ) -> bool:
        """Check if a refresh token has been revoked or replayed.

        A per-user revoke-all only invalidates tokens issued at or before the cut-off
        (``issued_at``); tokens from a later login stay valid.
        """
        now = time.time()

        if user_id and issued_at is not None:
            cutoff = await self.get_user_revoked_cutoff(user_id)
            if cutoff is not None and float(issued_at) <= cutoff:
                return True

        # 1. L1 Local Memory check
        async with self._lock:
            if jti in self._revoked_local:
                return True

        # 2. L2 Redis check
        try:
            val = await resilient_store.get(f"token:revoked:{jti}")
            if val is not None:
                async with self._lock:
                    self._revoked_local.add(jti)
                return True
        except Exception as err:
            logger.debug(f"[TokenStore] Redis check revoked failed: {err}")

        # 3. L3 PostgreSQL query
        try:
            async with async_session_factory() as session:
                stmt = select(RevokedTokenRecord).where(RevokedTokenRecord.jti == jti)
                result = await session.execute(stmt)
                record = result.scalars().first()
                if record:
                    # Sync to L1 and L2
                    async with self._lock:
                        self._revoked_local.add(jti)
                    ttl = max(1, int(record.expires_at.timestamp() - now)) if record.expires_at else 86400
                    try:
                        await resilient_store.set(f"token:revoked:{jti}", "1", expire_seconds=ttl)
                    except Exception:
                        pass
                    return True
        except Exception as err:
            logger.warning(f"[TokenStore] Database check revoked token '{jti}' failed: {err}")

        return False

    async def get_user_revoked_cutoff(self, user_id: str) -> Optional[float]:
        """Epoch of the latest revoke-all for this user, if any (L1, then L2)."""
        async with self._lock:
            local = self._user_revoked_at_local.get(user_id)
        try:
            remote = await resilient_store.get(f"user:revoked_all:{user_id}")
        except Exception as err:
            logger.debug(f"[TokenStore] Redis get user cut-off failed: {err}")
            remote = None
        values = [v for v in (local, float(remote) if remote is not None else None) if v is not None]
        if not values:
            return None
        cutoff = max(values)
        async with self._lock:
            self._user_revoked_at_local[user_id] = cutoff
        return cutoff

    async def revoke_session(
        self, sid: str, user_id: str, ttl_seconds: int, reason: str = "logout"
    ) -> None:
        """Revoke a login session (its access tokens and refresh chain).

        Checked on every authenticated request, so reads stay in L1/L2; the L3 row is kept
        for durability and audit. Without Redis, a revocation is per-process and lost on
        restart for the remaining access-token lifetime (the refresh chain stays revoked).
        """
        async with self._lock:
            self._revoked_sessions_local.add(sid)
        try:
            await resilient_store.set(f"session:revoked:{sid}", "1", expire_seconds=ttl_seconds)
        except Exception as err:
            logger.debug(f"[TokenStore] Redis session revocation failed: {err}")
        try:
            async with async_session_factory() as session:
                session.add(RevokedTokenRecord(
                    jti=sid,
                    user_id=user_id,
                    token_type="session",
                    reason=reason,
                    expires_at=_utc_from_timestamp(time.time() + ttl_seconds),
                ))
                await session.commit()
        except Exception as err:
            logger.debug(f"[TokenStore] Database session revocation record failed: {err}")

    async def is_session_revoked(self, sid: str) -> bool:
        async with self._lock:
            if sid in self._revoked_sessions_local:
                return True
        try:
            if await resilient_store.get(f"session:revoked:{sid}") is not None:
                async with self._lock:
                    self._revoked_sessions_local.add(sid)
                return True
        except Exception as err:
            logger.debug(f"[TokenStore] Redis session check failed: {err}")
        return False

    async def get_active_token(self, jti: str) -> Optional[Dict[str, Any]]:
        """Retrieve active token metadata if it is valid and unexpired."""
        now = time.time()

        # 1. L1 Local Memory check
        async with self._lock:
            cached = self._active_local.get(jti)
            if cached:
                if cached.get("expires_at", 0) > now:
                    return cached
                else:
                    self._active_local.pop(jti, None)
                    return None

        # 2. L2 Redis check
        try:
            val = await resilient_store.get(f"token:active:{jti}")
            if val:
                info = json.loads(val)
                if info.get("expires_at", 0) > now:
                    async with self._lock:
                        self._active_local[jti] = info
                    return info
        except Exception as err:
            logger.debug(f"[TokenStore] Redis get active token failed: {err}")

        # 3. L3 PostgreSQL query
        try:
            async with async_session_factory() as session:
                stmt = (
                    select(ActiveRefreshTokenRecord)
                    .where(ActiveRefreshTokenRecord.jti == jti)
                    .where(ActiveRefreshTokenRecord.expires_at > datetime.now(timezone.utc))
                )
                result = await session.execute(stmt)
                db_record = result.scalars().first()
                if db_record:
                    exp_ts = db_record.expires_at.timestamp()
                    token_info = {
                        "sub": db_record.user_id,
                        "role": db_record.role,
                        "email": db_record.email or "",
                        "expires_at": exp_ts,
                    }
                    async with self._lock:
                        self._active_local[jti] = token_info
                    ttl = max(1, int(exp_ts - now))
                    try:
                        await resilient_store.set(
                            f"token:active:{jti}",
                            json.dumps(token_info),
                            expire_seconds=ttl,
                        )
                    except Exception:
                        pass
                    return token_info
        except Exception as err:
            logger.warning(f"[TokenStore] Database query active token '{jti}' failed: {err}")

        return None

    async def revoke_token(
        self,
        jti: str,
        user_id: str,
        expires_at: float,
        reason: str = "logout",
    ) -> bool:
        """Revoke a single refresh token, marking it in the blacklist and removing active state."""
        now = time.time()
        ttl_seconds = max(1, int(expires_at - now)) if expires_at > now else 86400

        # 1. Update L1
        async with self._lock:
            self._active_local.pop(jti, None)
            self._revoked_local.add(jti)

        # 2. Update L2 Redis
        try:
            await resilient_store.delete(f"token:active:{jti}")
            await resilient_store.set(f"token:revoked:{jti}", "1", expire_seconds=ttl_seconds)
        except Exception as err:
            logger.debug(f"[TokenStore] Redis token revocation failed: {err}")

        # 3. Update L3 PostgreSQL
        try:
            async with async_session_factory() as session:
                # Remove from active
                await session.execute(
                    delete(ActiveRefreshTokenRecord).where(ActiveRefreshTokenRecord.jti == jti)
                )
                # Add to revoked blacklist
                rev_record = RevokedTokenRecord(
                    jti=jti,
                    user_id=user_id,
                    token_type="refresh",
                    reason=reason,
                    expires_at=_utc_from_timestamp(expires_at if expires_at > now else now + 86400),
                )
                session.add(rev_record)
                await session.commit()
            return True
        except Exception as err:
            logger.warning(f"[TokenStore] Database revocation record for '{jti}' failed: {err}")
            return True

    async def revoke_all_user_tokens(self, user_id: str, reason: str = "security_breach") -> int:
        """Revoke all active tokens for a given user (e.g. after replay attack or password change)."""
        now = time.time()
        revoked_count = 0

        # 1. Update L1
        async with self._lock:
            self._user_revoked_at_local[user_id] = now
            jtis_to_remove = [
                j for j, info in self._active_local.items() if info.get("sub") == user_id
            ]
            for j in jtis_to_remove:
                self._active_local.pop(j, None)
                self._revoked_local.add(j)
                revoked_count += 1

        # 2. Update L2 Redis
        try:
            # 7-day cutoff for any token issued prior to this
            await resilient_store.set(f"user:revoked_all:{user_id}", str(now), expire_seconds=7 * 86400)
            for j in jtis_to_remove:
                await resilient_store.delete(f"token:active:{j}")
                await resilient_store.set(f"token:revoked:{j}", "1", expire_seconds=7 * 86400)
        except Exception as err:
            logger.debug(f"[TokenStore] Redis revoke all user tokens failed: {err}")

        # 3. Update L3 PostgreSQL
        try:
            async with async_session_factory() as session:
                stmt = select(ActiveRefreshTokenRecord).where(
                    ActiveRefreshTokenRecord.user_id == user_id
                )
                result = await session.execute(stmt)
                records = result.scalars().all()

                for r in records:
                    rev_rec = RevokedTokenRecord(
                        jti=r.jti,
                        user_id=user_id,
                        token_type="refresh",
                        reason=reason,
                        expires_at=r.expires_at,
                    )
                    session.add(rev_rec)
                    revoked_count += 1

                await session.execute(
                    delete(ActiveRefreshTokenRecord).where(
                        ActiveRefreshTokenRecord.user_id == user_id
                    )
                )
                await session.commit()
        except Exception as err:
            logger.warning(
                f"[TokenStore] Database bulk revocation for user '{user_id}' failed: {err}"
            )

        return max(revoked_count, 1)

    async def cleanup_expired_tokens(self) -> int:
        """Periodically purge expired records from database tables to prevent table bloat."""
        now_dt = datetime.now(timezone.utc)
        try:
            async with async_session_factory() as session:
                del_active = await session.execute(
                    delete(ActiveRefreshTokenRecord).where(
                        ActiveRefreshTokenRecord.expires_at < now_dt
                    )
                )
                del_revoked = await session.execute(
                    delete(RevokedTokenRecord).where(RevokedTokenRecord.expires_at < now_dt)
                )
                await session.commit()
                purged = (del_active.rowcount or 0) + (del_revoked.rowcount or 0)
                logger.info(f"[TokenStore] Purged {purged} expired token session records.")
                return purged
        except Exception as err:
            logger.debug(f"[TokenStore] Periodic expired token purge skipped: {err}")
            return 0


# Global distributed token store singleton
token_store = DistributedTokenStore()

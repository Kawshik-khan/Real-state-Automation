"""Brute Force Protection & Progressive Account Lockout.

Defends authentication endpoints against credential stuffing and automated
password attacks. Applies progressive response delays on repeated failures
and locks out compromised targets for 15 minutes upon reaching 5 failures.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Tuple

from app.core.redis_client import resilient_store


class AccountLockoutService:
    """Manages failed authentication tracking, progressive delay, and temporary lockouts."""

    def __init__(self, max_failures: int = 5, lockout_duration_seconds: int = 900):
        self.max_failures = max_failures
        self.lockout_duration_seconds = lockout_duration_seconds
        
        # In-memory fallbacks: email -> {"count": int, "last_attempt": float, "locked_until": float}
        self._local_records: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, email: str, ip: str) -> str:
        return email.strip().lower()

    async def check_lockout(self, email: str, ip: str) -> Tuple[bool, int]:
        """Check if account is currently locked."""
        now = time.time()
        key = self._get_key(email, ip)

        # 1. Check in-memory store
        record = self._local_records.get(key)
        if record:
            locked_until = record.get("locked_until", 0.0)
            if locked_until > now:
                remaining = int(locked_until - now)
                return True, max(1, remaining)

        # 2. Check resilient Redis store
        try:
            redis_lock = await resilient_store.get(f"auth_lockout:{key}")
            if redis_lock:
                locked_until = float(redis_lock.get("locked_until", 0.0))
                if locked_until > now:
                    remaining = int(locked_until - now)
                    return True, max(1, remaining)
        except Exception:
            pass

        return False, 0

    async def record_failure(self, email: str, ip: str) -> Tuple[int, float, bool]:
        """Record a failed login attempt."""
        now = time.time()
        key = self._get_key(email, ip)
        
        async with self._lock:
            record = self._local_records.get(key, {"count": 0, "last_attempt": now, "locked_until": 0.0})
            
            # Reset counter if last attempt was older than lockout window
            if (now - record["last_attempt"]) > self.lockout_duration_seconds:
                record["count"] = 0
                record["locked_until"] = 0.0

            record["count"] += 1
            record["last_attempt"] = now
            attempts = record["count"]

            is_locked = False
            delay = 0.0

            if attempts >= self.max_failures:
                record["locked_until"] = now + self.lockout_duration_seconds
                is_locked = True
            elif attempts in (3, 4):
                # Progressive delay to stall credential stuffers
                delay = (attempts - 2) * 0.75

            self._local_records[key] = record

        # Sync to resilient Redis
        try:
            if is_locked:
                await resilient_store.set(
                    f"auth_lockout:{key}",
                    {"email": email, "locked_until": now + self.lockout_duration_seconds},
                    ttl=self.lockout_duration_seconds,
                )
            else:
                await resilient_store.set(
                    f"auth_attempts:{key}",
                    {"count": attempts, "last_attempt": now},
                    ttl=self.lockout_duration_seconds,
                )
        except Exception:
            pass

        return attempts, delay, is_locked

    async def record_success(self, email: str, ip: str) -> None:
        """Clear failed attempts upon successful login."""
        key = self._get_key(email, ip)
        async with self._lock:
            self._local_records.pop(key, None)

        try:
            await resilient_store.delete(f"auth_attempts:{key}")
            await resilient_store.delete(f"auth_lockout:{key}")
        except Exception:
            pass

    async def unlock_account(self, email: str) -> int:
        """Unlock all records for given email (admin action)."""
        clean_email = email.strip().lower()
        unlocked_count = 0

        async with self._lock:
            if clean_email in self._local_records:
                self._local_records.pop(clean_email, None)
                unlocked_count += 1

        try:
            await resilient_store.delete(f"auth_attempts:{clean_email}")
            await resilient_store.delete(f"auth_lockout:{clean_email}")
        except Exception:
            pass

        return unlocked_count

    def get_locked_accounts(self) -> List[Dict[str, Any]]:
        """List active locked accounts for developer/admin view."""
        now = time.time()
        locked = []
        for key, rec in self._local_records.items():
            locked_until = rec.get("locked_until", 0.0)
            if locked_until > now:
                locked.append({
                    "email": key,
                    "remaining_seconds": int(locked_until - now),
                    "failed_attempts": rec.get("count", 0),
                })
        return locked


# Singleton instance
account_lockout = AccountLockoutService()

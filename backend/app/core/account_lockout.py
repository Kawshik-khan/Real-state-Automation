"""Brute-force protection for the login endpoint.

Failures are counted per (email, client IP): 5 failures within 15 min lock that email for
that IP only. The account itself is never locked, so an attacker who knows a victim's email
cannot lock the victim out from the victim's own network. Password spraying across emails is
bounded by the per-IP login rate limit (``AUTH_LOGIN_LIMIT``).

There is deliberately no IP-wide lock: if the client IP were mis-resolved behind a proxy
(every request appearing to come from the proxy), an IP-wide lock would lock out all users.

State lives in ``resilient_store`` (Redis when configured) so limits hold across workers.
"""

import time
from typing import Any, Dict, List, Tuple

from app.core.redis_client import resilient_store


class AccountLockoutService:
    def __init__(self, max_failures: int = 5, lockout_duration_seconds: int = 900):
        self.max_failures = max_failures
        self.lockout_duration_seconds = lockout_duration_seconds
        # Per-process mirror used only for the admin "locked accounts" listing.
        self._recent_locks: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _pair(email: str, ip: str) -> str:
        return f"{email.strip().lower()}|{ip}"

    async def _lock_remaining(self, key: str, email: str = "") -> int:
        started = await resilient_store.get(key)
        if not started:
            return 0
        started_at = float(started)
        if email:
            unlocked_at = await resilient_store.get(f"auth_unlocked_at:{email}")
            if unlocked_at and float(unlocked_at) >= started_at:
                return 0
        return max(0, int(started_at + self.lockout_duration_seconds - time.time()))

    async def check_lockout(self, email: str, ip: str) -> Tuple[bool, int]:
        """Return (is_locked, remaining_seconds) for this email from this IP."""
        email = email.strip().lower()
        remaining = await self._lock_remaining(f"auth_lock:{self._pair(email, ip)}", email)
        return remaining > 0, remaining

    async def record_failure(self, email: str, ip: str) -> Tuple[int, bool]:
        """Record a failed login. Returns (attempts_for_pair, newly_locked)."""
        email = email.strip().lower()
        window = self.lockout_duration_seconds
        now = str(time.time())

        _, pair_attempts, _ = await resilient_store.sliding_window_increment(
            f"auth_fail:{self._pair(email, ip)}", window, self.max_failures
        )

        newly_locked = False
        if pair_attempts >= self.max_failures:
            await resilient_store.set(f"auth_lock:{self._pair(email, ip)}", now, expire_seconds=window)
            self._recent_locks[self._pair(email, ip)] = {"email": email, "ip": ip, "locked_at": float(now),
                                                         "failed_attempts": pair_attempts}
            newly_locked = True
        return pair_attempts, newly_locked

    async def record_success(self, email: str, ip: str) -> None:
        pair = self._pair(email, ip)
        await resilient_store.reset_window(f"auth_fail:{pair}")
        self._recent_locks.pop(pair, None)

    async def unlock_account(self, email: str) -> int:
        """Admin action: clear every IP lock for this email (across workers via the store)."""
        email = email.strip().lower()
        await resilient_store.set(f"auth_unlocked_at:{email}", str(time.time()),
                                  expire_seconds=self.lockout_duration_seconds)
        cleared = [k for k, v in self._recent_locks.items() if v["email"] == email]
        for key in cleared:
            self._recent_locks.pop(key, None)
            await resilient_store.reset_window(f"auth_fail:{key}")
        return len(cleared)

    def get_locked_accounts(self) -> List[Dict[str, Any]]:
        """Locks recorded by this worker (for the admin/developer view)."""
        now = time.time()
        locked = []
        for rec in self._recent_locks.values():
            remaining = int(rec["locked_at"] + self.lockout_duration_seconds - now)
            if remaining > 0:
                locked.append({
                    "email": rec["email"],
                    "ip": rec["ip"],
                    "remaining_seconds": remaining,
                    "failed_attempts": rec["failed_attempts"],
                })
        return locked


account_lockout = AccountLockoutService()

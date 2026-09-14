"""Redis Connection & In-Memory Resilient Store for Sliding-Window Rate Limiting and Session State.

Provides a unified interface that leverages Redis when available/configured (via REDIS_URL),
and seamlessly falls back to a thread-safe, high-performance in-memory store if Redis is offline
or not installed. This guarantees zero breaking changes in development, testing, and cloud deployments.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class InMemoryStore:
    """Thread-safe and async-safe in-memory sliding-window counter and key-value store."""

    def __init__(self):
        self._sliding_windows: Dict[str, List[float]] = {}
        self._key_values: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expire_timestamp)
        self._lock = asyncio.Lock()

    async def sliding_window_increment(
        self, key: str, window_seconds: int, max_limit: int
    ) -> Tuple[bool, int, int]:
        """Sliding-window counter: returns (is_allowed, current_count, retry_after_seconds)."""
        async with self._lock:
            now = time.time()
            cutoff = now - window_seconds

            # Retrieve and prune expired timestamps
            timestamps = self._sliding_windows.get(key, [])
            timestamps = [ts for ts in timestamps if ts > cutoff]

            current_count = len(timestamps)

            if current_count < max_limit:
                timestamps.append(now)
                self._sliding_windows[key] = timestamps
                return True, current_count + 1, 0
            else:
                self._sliding_windows[key] = timestamps
                oldest = timestamps[0] if timestamps else now
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, current_count, retry_after

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Store key-value with optional TTL."""
        async with self._lock:
            expire_at = time.time() + expire_seconds if expire_seconds else float("inf")
            self._key_values[key] = (value, expire_at)
            return True

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve key value if not expired."""
        async with self._lock:
            item = self._key_values.get(key)
            if not item:
                return None
            val, expire_at = item
            if time.time() > expire_at:
                del self._key_values[key]
                return None
            return val

    async def delete(self, key: str) -> bool:
        """Delete key from store."""
        async with self._lock:
            self._key_values.pop(key, None)
            self._sliding_windows.pop(key, None)
            return True


class ResilientRedisClient:
    """Unified Redis client with transparent in-memory fallback."""

    def __init__(self):
        self._redis = None
        self._in_memory = InMemoryStore()
        self._is_redis_available = False
        self._has_initialized = False

    async def initialize(self):
        """Attempt to connect to Redis if configured."""
        if self._has_initialized:
            return

        redis_url = getattr(settings, "redis_url", None)
        if not redis_url:
            logger.info("[ResilientStore] No REDIS_URL configured; using in-memory resilient store.")
            self._has_initialized = True
            return

        try:
            import redis.asyncio as aioredis  # type: ignore

            self._redis = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=3.0,
            )
            await self._redis.ping()
            self._is_redis_available = True
            logger.info("[ResilientStore] Successfully connected to Redis cluster.")
        except Exception as err:
            logger.warning(
                f"[ResilientStore] Redis unavailable ({err}); activating in-memory fallback."
            )
            self._is_redis_available = False
        finally:
            self._has_initialized = True

    async def sliding_window_increment(
        self, key: str, window_seconds: int = 60, max_limit: int = 100
    ) -> Tuple[bool, int, int]:
        """Sliding-window counter across rolling window_seconds."""
        if not self._has_initialized:
            await self.initialize()

        if not self._is_redis_available or not self._redis:
            return await self._in_memory.sliding_window_increment(key, window_seconds, max_limit)

        try:
            now = time.time()
            cutoff = now - window_seconds
            zset_key = f"rl:{key}"

            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(zset_key, 0, cutoff)
            pipe.zcard(zset_key)
            results = await pipe.execute()

            current_count = results[1]
            if current_count < max_limit:
                pipe = self._redis.pipeline()
                pipe.zadd(zset_key, {str(uuid.uuid4()): now})
                pipe.expire(zset_key, window_seconds * 2)
                await pipe.execute()
                return True, current_count + 1, 0
            else:
                oldest_entries = await self._redis.zrange(zset_key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_ts = oldest_entries[0][1]
                    retry_after = max(1, int(oldest_ts + window_seconds - now))
                else:
                    retry_after = 1
                return False, current_count, retry_after
        except Exception as err:
            logger.warning(f"[ResilientStore] Redis sliding-window failed ({err}); using in-memory.")
            return await self._in_memory.sliding_window_increment(key, window_seconds, max_limit)

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Store key-value with TTL."""
        if not self._has_initialized:
            await self.initialize()

        if not self._is_redis_available or not self._redis:
            return await self._in_memory.set(key, value, expire_seconds)

        try:
            if expire_seconds:
                await self._redis.setex(key, expire_seconds, str(value))
            else:
                await self._redis.set(key, str(value))
            return True
        except Exception:
            return await self._in_memory.set(key, value, expire_seconds)

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve key-value."""
        if not self._has_initialized:
            await self.initialize()

        if not self._is_redis_available or not self._redis:
            return await self._in_memory.get(key)

        try:
            return await self._redis.get(key)
        except Exception:
            return await self._in_memory.get(key)

    async def delete(self, key: str) -> bool:
        """Delete key."""
        if not self._has_initialized:
            await self.initialize()

        if not self._is_redis_available or not self._redis:
            return await self._in_memory.delete(key)

        try:
            await self._redis.delete(key)
            return True
        except Exception:
            return await self._in_memory.delete(key)


# Global singleton instance
resilient_store = ResilientRedisClient()

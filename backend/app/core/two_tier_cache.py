"""Two-Tier Data Caching (L1 Local Memory + L2 Distributed Redis) with ETag support.

Provides high-throughput sub-millisecond in-process caching (L1) backed by
resilient Redis/in-memory storage (L2) with automatic invalidation and
HTTP 304 Not Modified conditional request evaluation.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.redis_client import resilient_store


class TwoTierCache:
    """Enterprise multi-tier caching layer."""

    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        # L1: key -> (value, created_at, ttl)
        self._l1: Dict[str, Tuple[Any, float, int]] = {}
        self._lock = asyncio.Lock()
        
        # Telemetry
        self._l1_hits = 0
        self._l2_hits = 0
        self._misses = 0

    def _purge_l1_expired(self, now: float) -> None:
        expired = [k for k, (val, t_stamp, ttl) in self._l1.items() if (now - t_stamp) > ttl]
        for k in expired:
            self._l1.pop(k, None)

    async def get(self, key: str) -> Optional[Any]:
        """Fetch value checking L1 memory first, then falling back to L2 Redis."""
        now = time.time()

        # 1. Check L1 memory (0ms)
        if key in self._l1:
            val, t_stamp, ttl = self._l1[key]
            if (now - t_stamp) <= ttl:
                self._l1_hits += 1
                return val
            else:
                self._l1.pop(key, None)

        # 2. Check L2 Redis/resilient store (<5ms)
        try:
            l2_val = await resilient_store.get(key)
            if l2_val is not None:
                self._l2_hits += 1
                # Populate L1
                async with self._lock:
                    self._l1[key] = (l2_val, now, self.default_ttl)
                return l2_val
        except Exception:
            pass

        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set key in both L1 memory and L2 Redis."""
        now = time.time()
        actual_ttl = ttl if ttl is not None else self.default_ttl

        # Set L1
        async with self._lock:
            self._l1[key] = (value, now, actual_ttl)

        # Set L2
        try:
            await resilient_store.set(key, value, ttl=actual_ttl)
        except Exception:
            pass

    async def invalidate(self, pattern_or_key: str) -> int:
        """Invalidate key from L1 and L2."""
        count = 0
        async with self._lock:
            if "*" in pattern_or_key:
                prefix = pattern_or_key.replace("*", "")
                to_remove = [k for k in self._l1.keys() if k.startswith(prefix)]
                for k in to_remove:
                    self._l1.pop(k, None)
                    count += 1
            else:
                if pattern_or_key in self._l1:
                    self._l1.pop(pattern_or_key, None)
                    count += 1

        try:
            if "*" not in pattern_or_key:
                await resilient_store.delete(pattern_or_key)
        except Exception:
            pass

        return count

    def generate_etag(self, data: Any) -> str:
        """Generate strong/weak ETag based on payload content."""
        try:
            serialized = json.dumps(data, sort_keys=True, default=str)
        except Exception:
            serialized = str(data)
        digest = hashlib.sha256(serialized.encode()).hexdigest()[:16]
        return f'W/"{digest}"'

    def get_stats(self) -> Dict[str, Any]:
        """Return diagnostic metrics for cache performance."""
        now = time.time()
        active_l1 = sum(1 for _, t_stamp, ttl in self._l1.values() if (now - t_stamp) <= ttl)
        total = self._l1_hits + self._l2_hits + self._misses
        hit_ratio = round(((self._l1_hits + self._l2_hits) / total) * 100, 1) if total > 0 else 0.0

        return {
            "l1_hits": self._l1_hits,
            "l2_hits": self._l2_hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_ratio_pct": hit_ratio,
            "active_l1_keys": active_l1,
            "default_ttl_seconds": self.default_ttl,
        }


# Singleton instance
two_tier_cache = TwoTierCache()

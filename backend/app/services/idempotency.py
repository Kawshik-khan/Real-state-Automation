"""Idempotency & De-duplication Service — Prevents double-processing of incoming webhooks."""

import time
from typing import Dict, Optional


class IdempotencyService:
    """In-memory idempotency cache with TTL expiration.
    
    Can be seamlessly swapped or backed by Redis / PostgreSQL key store.
    """

    def __init__(self, default_ttl_seconds: int = 86400):  # 24 hours default
        self._cache: Dict[str, float] = {}
        self.default_ttl = default_ttl_seconds

    def is_processed(self, key: str) -> bool:
        """Check if message_id key has already been processed and is within TTL."""
        if not key:
            return False
        
        now = time.time()
        expiry = self._cache.get(key)
        if expiry is None:
            return False
        
        if now > expiry:
            # Expired, clean up
            del self._cache[key]
            return False
        
        return True

    def record_processed(self, key: str, ttl_seconds: Optional[int] = None) -> None:
        """Record message_id key as processed with an expiration timestamp."""
        if not key:
            return
        
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = time.time() + ttl

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()


# Global singleton instance
idempotency_service = IdempotencyService()

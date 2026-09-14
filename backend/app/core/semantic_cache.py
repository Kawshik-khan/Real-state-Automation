"""Semantic Vector Caching for LLM & Agent Invocations.

Accelerates repeated natural language real estate queries (e.g. pricing,
amenities, payment plans) by matching question embeddings using cosine similarity.
Eliminates redundant LLM API calls and delivers sub-20ms cached responses.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.core.redis_client import resilient_store
from app.services.llm import llm_service


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = 0.0
    norm_a_sq = 0.0
    norm_b_sq = 0.0
    for a, b in zip(vec_a, vec_b):
        dot_product += a * b
        norm_a_sq += a * a
        norm_b_sq += b * b
    if norm_a_sq <= 0.0 or norm_b_sq <= 0.0:
        return 0.0
    return dot_product / (math.sqrt(norm_a_sq) * math.sqrt(norm_b_sq))


@dataclass
class SemanticCacheEntry:
    key: str
    query: str
    vector: List[float]
    response_data: Dict[str, Any]
    tenant_id: str
    language: str
    intent: str
    created_at: float
    ttl: int = 3600
    tokens_saved_estimate: int = 180

    def is_expired(self, now: float) -> bool:
        return (now - self.created_at) > self.ttl


class SemanticCacheManager:
    """In-memory & distributed semantic vector cache orchestrator."""

    def __init__(self, default_threshold: float = 0.88, default_ttl: int = 3600):
        self.default_threshold = default_threshold
        self.default_ttl = default_ttl
        self._cache: Dict[str, SemanticCacheEntry] = {}
        self._lock = asyncio.Lock()
        
        # Telemetry metrics
        self._hits = 0
        self._misses = 0
        self._tokens_saved = 0

    def _purge_expired(self, now: float) -> None:
        expired_keys = [k for k, v in self._cache.items() if v.is_expired(now)]
        for k in expired_keys:
            self._cache.pop(k, None)

    async def lookup(
        self,
        query: str,
        tenant_id: str = "glg-default",
        language: str = "en",
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """Look up semantically equivalent cached response for query."""
        if not query or not query.strip():
            return None

        clean_q = query.strip()
        sim_threshold = threshold if threshold is not None else self.default_threshold
        now = time.time()

        # 1. Exact string match fast-path
        query_hash = hashlib.sha256(f"{tenant_id}:{language}:{clean_q.lower()}".encode()).hexdigest()[:16]
        entry = self._cache.get(query_hash)
        if entry and not entry.is_expired(now):
            self._hits += 1
            self._tokens_saved += entry.tokens_saved_estimate
            return entry.response_data, 1.0

        # 2. Vector embedding similarity lookup
        try:
            query_vec = await llm_service.embed(clean_q)
        except Exception:
            self._misses += 1
            return None

        if not query_vec:
            self._misses += 1
            return None

        best_sim = -1.0
        best_entry: Optional[SemanticCacheEntry] = None

        self._purge_expired(now)

        for e in self._cache.values():
            if e.tenant_id != tenant_id:
                continue
            if e.is_expired(now):
                continue

            sim = cosine_similarity(query_vec, e.vector)
            if sim > best_sim:
                best_sim = sim
                best_entry = e

        if best_entry and best_sim >= sim_threshold:
            self._hits += 1
            self._tokens_saved += best_entry.tokens_saved_estimate
            return best_entry.response_data, best_sim

        self._misses += 1
        return None

    async def store(
        self,
        query: str,
        response_data: Dict[str, Any],
        tenant_id: str = "glg-default",
        language: str = "en",
        intent: str = "property_search",
        ttl: Optional[int] = None,
    ) -> None:
        """Store query and response into semantic vector cache."""
        if not query or not response_data:
            return

        # Do not cache escalation responses or dynamic booking confirmations
        if response_data.get("requires_escalation") or intent in ("booking", "escalation"):
            return

        clean_q = query.strip()
        now = time.time()
        actual_ttl = ttl if ttl is not None else self.default_ttl

        try:
            query_vec = await llm_service.embed(clean_q)
        except Exception:
            return

        if not query_vec:
            return

        query_hash = hashlib.sha256(f"{tenant_id}:{language}:{clean_q.lower()}".encode()).hexdigest()[:16]
        entry = SemanticCacheEntry(
            key=query_hash,
            query=clean_q,
            vector=query_vec,
            response_data=response_data,
            tenant_id=tenant_id,
            language=language,
            intent=intent,
            created_at=now,
            ttl=actual_ttl,
        )

        async with self._lock:
            self._cache[query_hash] = entry

        # Optionally store in resilient Redis for cross-replica distribution
        try:
            await resilient_store.set(
                f"semantic_cache:{tenant_id}:{query_hash}",
                {
                    "query": clean_q,
                    "response_data": response_data,
                    "intent": intent,
                    "language": language,
                },
                ttl=actual_ttl,
            )
        except Exception:
            pass

    async def invalidate_by_intent(self, intent: str, tenant_id: Optional[str] = None) -> int:
        """Invalidate cached entries matching specific intent (e.g. on property price updates)."""
        removed = 0
        async with self._lock:
            to_remove = [
                k for k, v in self._cache.items()
                if v.intent == intent and (tenant_id is None or v.tenant_id == tenant_id)
            ]
            for k in to_remove:
                self._cache.pop(k, None)
                removed += 1
        return removed

    async def invalidate_all(self) -> int:
        """Flush all entries from semantic cache."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Return diagnostic metrics for developer telemetry."""
        now = time.time()
        active_entries = sum(1 for e in self._cache.values() if not e.is_expired(now))
        total_lookups = self._hits + self._misses
        hit_ratio = round((self._hits / total_lookups) * 100, 1) if total_lookups > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_lookups": total_lookups,
            "hit_ratio_pct": hit_ratio,
            "active_entries": active_entries,
            "tokens_saved_estimate": self._tokens_saved,
            "default_similarity_threshold": self.default_threshold,
            "default_ttl_seconds": self.default_ttl,
        }


# Singleton instance
semantic_cache = SemanticCacheManager()

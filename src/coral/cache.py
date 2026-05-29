"""
CoralCache — Single Responsibility Principle (SRP)
This module only handles caching. Nothing else.
Coral feature: Smart TTL caching so repeated queries are fast.
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    """A single cached query result."""
    query_hash: str
    result: list[dict]
    created_at: float
    ttl_seconds: int
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class CoralCache:
    """
    TTL-based in-memory cache for Coral SQL query results.
    Coral feature: Smart caching — repeated queries served from cache,
    never hitting the API twice within the TTL window.
    """

    def __init__(self, ttl_seconds: int = 300):
        self._store: dict[str, CacheEntry] = {}
        self._ttl = ttl_seconds
        self._total_hits = 0
        self._total_misses = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, query: str) -> list[dict] | None:
        """Return cached result if exists and not expired, else None."""
        key = self._hash(query)
        entry = self._store.get(key)

        if entry is None or entry.is_expired:
            self._total_misses += 1
            if entry and entry.is_expired:
                del self._store[key]
            return None

        entry.hit_count += 1
        self._total_hits += 1
        return entry.result

    def set(self, query: str, result: list[dict]) -> None:
        """Cache a query result with the configured TTL."""
        key = self._hash(query)
        self._store[key] = CacheEntry(
            query_hash=key,
            result=result,
            created_at=time.time(),
            ttl_seconds=self._ttl,
        )

    def invalidate(self, query: str) -> None:
        """Remove a specific query from cache."""
        key = self._hash(query)
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear entire cache."""
        self._store.clear()

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Return cache performance statistics."""
        total = self._total_hits + self._total_misses
        hit_rate = (self._total_hits / total * 100) if total > 0 else 0
        return {
            "total_entries": len(self._store),
            "total_hits": self._total_hits,
            "total_misses": self._total_misses,
            "hit_rate_pct": round(hit_rate, 1),
            "ttl_seconds": self._ttl,
        }

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _hash(query: str) -> str:
        """Deterministic hash of a SQL query string."""
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]

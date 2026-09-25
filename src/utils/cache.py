"""In-process TTL cache for dictionary-like API data (statuses, types, schemas...)."""

import asyncio
import copy
import logging
import os
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL_SECONDS = 600
CACHE_TTL_ENV = "OPENPROJECT_CACHE_TTL"

_MISSING = object()


def ttl_from_env(env: Optional[Dict[str, str]] = None) -> float:
    """Read the TTL from OPENPROJECT_CACHE_TTL (default 600 s, 0 disables the cache)."""
    env = os.environ if env is None else env
    raw = env.get(CACHE_TTL_ENV)
    if raw is None or raw.strip() == "":
        return DEFAULT_CACHE_TTL_SECONDS
    try:
        return max(0.0, float(raw))
    except ValueError:
        logger.warning(
            f"Invalid {CACHE_TTL_ENV}={raw!r}, using default {DEFAULT_CACHE_TTL_SECONDS}s"
        )
        return DEFAULT_CACHE_TTL_SECONDS


class TTLCache:
    """Async TTL cache with a per-key lock, so concurrent misses trigger a single fetch.

    Values are returned as deep copies, so callers may mutate them freely.
    Exceptions raised by the factory are not cached.
    """

    def __init__(
        self,
        ttl: Optional[float] = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.ttl = ttl_from_env() if ttl is None else ttl
        self._clock = clock
        self._entries: Dict[str, Tuple[float, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    @property
    def enabled(self) -> bool:
        return self.ttl > 0

    def _lookup(self, key: str) -> Any:
        entry = self._entries.get(key)
        if entry is None:
            return _MISSING
        expires_at, value = entry
        if self._clock() >= expires_at:
            del self._entries[key]
            return _MISSING
        return value

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[Any]]) -> Any:
        """Return the cached value for `key` or await `factory()` and cache its result."""
        if not self.enabled:
            return await factory()

        value = self._lookup(key)
        if value is not _MISSING:
            return copy.deepcopy(value)

        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            value = self._lookup(key)
            if value is _MISSING:
                value = await factory()
                self._entries[key] = (self._clock() + self.ttl, value)
        return copy.deepcopy(value)

    def invalidate(self, key: str) -> None:
        """Remove a single key."""
        self._entries.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()
        self._locks.clear()

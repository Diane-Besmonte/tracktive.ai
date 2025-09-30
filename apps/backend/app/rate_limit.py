from __future__ import annotations
import asyncio
import time
from contextlib import asynccontextmanager

class AlreadyRunning(Exception):
    """Raised when an identical request is already in flight."""
    pass

class SingleFlight:
    """
    In-memory single-flight guard (per-process).
    Prevents concurrent runs for the same key.
    """
    def __init__(self, ttl: float = 300.0):
        self._inflight: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._ttl = ttl  # cleanup stale locks after ttl seconds

    async def _cleanup(self) -> None:
        now = time.time()
        stale = [k for k, ts in self._inflight.items() if now - ts > self._ttl]
        for k in stale:
            self._inflight.pop(k, None)

    async def acquire(self, key: str) -> bool:
        async with self._lock:
            await self._cleanup()
            if key in self._inflight:
                return False
            self._inflight[key] = time.time()
            return True

    async def release(self, key: str) -> None:
        async with self._lock:
            self._inflight.pop(key, None)

    @asynccontextmanager
    async def guard(self, key: str):
        ok = await self.acquire(key)
        if not ok:
            raise AlreadyRunning(f"in-flight: {key}")
        try:
            yield
        finally:
            await self.release(key)

singleflight = SingleFlight(ttl=300.0)

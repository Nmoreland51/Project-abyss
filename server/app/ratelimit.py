"""Small in-process sliding-window rate limiter.

Scope: single-process pilot deployments. Multi-process or multi-host deployments must add
limits at the reverse proxy (see docs/OPERATIONS.md); this is not a distributed limiter."""

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from .config import get_settings
from .errors import ApiError


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: float = 60.0) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                raise ApiError(429, "rate_limited", "Too many requests; slow down and retry later")
            hits.append(now)
            if len(self._hits) > 50_000:  # bound memory under key-spraying
                self._hits.clear()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    if get_settings().trust_proxy_headers:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

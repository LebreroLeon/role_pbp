import logging
import time
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Sliding-window rate limiter for development; replace with Redis in production."""

    def __init__(self) -> None:
        self._events: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._events[key]
            self._events[key] = [ts for ts in timestamps if ts > cutoff]
            if len(self._events[key]) >= limit:
                logger.warning("Rate limit exceeded for key=%s limit=%s/%ss", key, limit, window_seconds)
                return False
            self._events[key].append(now)
            return True


rate_limiter = InMemoryRateLimiter()

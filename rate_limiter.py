"""
Sliding-window rate limiter backed by in-memory storage.
Thread-safe for single-process deployments (asyncio).
"""
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        # key → list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean(self, key: str) -> None:
        cutoff = time.time() - self.window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def is_allowed(self, key: str) -> bool:
        self._clean(key)
        if len(self._requests[key]) < self.max_requests:
            self._requests[key].append(time.time())
            return True
        return False

    def retry_after(self, key: str) -> float:
        """Seconds until the oldest request falls outside the window."""
        self._clean(key)
        if not self._requests[key]:
            return 0.0
        oldest = min(self._requests[key])
        return max(0.0, round(oldest + self.window - time.time(), 1))

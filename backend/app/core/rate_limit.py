"""In-memory sliding-window rate limits for login and other account endpoints.

Kept per process: with several API workers each one counts separately, so the
real limit is `limit x workers`. Move the counters to Redis if that matters.
"""

import math
import time
from collections import deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import TooManyRequestsError

# Above this many tracked keys, idle ones are swept so memory stays bounded.
_SWEEP_THRESHOLD = 10_000


class RateLimiter:
    """At most `limit` hits per `key` within any `window_seconds` window."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    def check(self, key: str) -> None:
        """Raise if `key` is already at its limit, without counting a hit."""
        if not get_settings().rate_limit_enabled:
            return
        hits = self._recent(key)
        if len(hits) >= self.limit:
            raise TooManyRequestsError(self._retry_after(hits))

    def hit(self, key: str) -> None:
        """Count one hit for `key`, raising if that goes over the limit."""
        if not get_settings().rate_limit_enabled:
            return
        self.check(key)
        self._hits.setdefault(key, deque()).append(self._clock())
        if len(self._hits) > _SWEEP_THRESHOLD:
            self._sweep()

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)

    def clear(self) -> None:
        self._hits.clear()

    def _recent(self, key: str) -> deque[float]:
        hits = self._hits.get(key)
        if hits is None:
            return deque()
        cutoff = self._clock() - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if not hits:
            del self._hits[key]
        return hits

    def _retry_after(self, hits: deque[float]) -> int:
        """Seconds until the oldest hit leaves the window."""
        return max(1, math.ceil(hits[0] + self.window_seconds - self._clock()))

    def _sweep(self) -> None:
        for key in list(self._hits):
            self._recent(key)


# Login: per IP counts every attempt; per email counts only failed ones, and a
# successful login clears it. Together they stop guessing one account's
# password and spraying many accounts from one address.
login_by_ip = RateLimiter(limit=20, window_seconds=5 * 60)
login_failures_by_email = RateLimiter(limit=5, window_seconds=15 * 60)
register_by_ip = RateLimiter(limit=10, window_seconds=60 * 60)
# Each request sends an email, so these are tight to stop inbox flooding.
forgot_password_by_ip = RateLimiter(limit=5, window_seconds=15 * 60)
forgot_password_by_email = RateLimiter(limit=3, window_seconds=60 * 60)
resend_verification_by_user = RateLimiter(limit=3, window_seconds=60 * 60)
# Submitting link tokens (reset password, verify email).
link_tokens_by_ip = RateLimiter(limit=20, window_seconds=15 * 60)
# Wrong "current password" on settings actions: stops a stolen access token
# being used to guess the password.
password_confirm_failures_by_user = RateLimiter(limit=5, window_seconds=15 * 60)

ALL_LIMITERS = (
    login_by_ip,
    login_failures_by_email,
    register_by_ip,
    forgot_password_by_ip,
    forgot_password_by_email,
    resend_verification_by_user,
    link_tokens_by_ip,
    password_confirm_failures_by_user,
)


def client_ip(request: Request) -> str:
    """The direct peer's address. Behind a reverse proxy, run uvicorn with
    --proxy-headers and --forwarded-allow-ips so this is the real client."""
    return request.client.host if request.client else "unknown"

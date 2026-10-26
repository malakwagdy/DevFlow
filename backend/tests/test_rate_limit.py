import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.exceptions import TooManyRequestsError
from app.core.rate_limit import RateLimiter
from tests.conftest import REGISTER_PAYLOAD, register_user

EMAIL = REGISTER_PAYLOAD["email"]
PASSWORD = REGISTER_PAYLOAD["password"]


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


# --- RateLimiter --------------------------------------------------------------


def test_limiter_allows_up_to_the_limit() -> None:
    limiter = RateLimiter(limit=3, window_seconds=60, clock=_Clock())
    for _ in range(3):
        limiter.hit("k")
    with pytest.raises(TooManyRequestsError) as error:
        limiter.hit("k")
    assert error.value.headers == {"Retry-After": "60"}


def test_limiter_keys_are_independent() -> None:
    limiter = RateLimiter(limit=1, window_seconds=60, clock=_Clock())
    limiter.hit("a")
    limiter.hit("b")
    with pytest.raises(TooManyRequestsError):
        limiter.hit("a")


def test_limiter_window_slides() -> None:
    clock = _Clock()
    limiter = RateLimiter(limit=2, window_seconds=60, clock=clock)
    limiter.hit("k")
    clock.now += 30
    limiter.hit("k")
    clock.now += 31  # the first hit has left the window
    limiter.hit("k")
    with pytest.raises(TooManyRequestsError) as error:
        limiter.hit("k")
    assert error.value.headers == {"Retry-After": "29"}


def test_limiter_check_does_not_count() -> None:
    limiter = RateLimiter(limit=1, window_seconds=60, clock=_Clock())
    limiter.check("k")
    limiter.check("k")
    limiter.hit("k")
    with pytest.raises(TooManyRequestsError):
        limiter.check("k")


def test_limiter_reset() -> None:
    limiter = RateLimiter(limit=1, window_seconds=60, clock=_Clock())
    limiter.hit("k")
    limiter.reset("k")
    limiter.hit("k")


def test_limiter_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", False)
    limiter = RateLimiter(limit=1, window_seconds=60, clock=_Clock())
    for _ in range(5):
        limiter.hit("k")


# --- endpoints ----------------------------------------------------------------


async def _login(client: AsyncClient, password: str, email: str = EMAIL):
    return await client.post("/auth/login", json={"email": email, "password": password})


@pytest.mark.asyncio
async def test_repeated_wrong_passwords_lock_the_email(client: AsyncClient) -> None:
    await register_user(client)
    for _ in range(5):
        assert (await _login(client, "wrong-password")).status_code == 401

    response = await _login(client, PASSWORD)  # even the right password
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many attempts. Please try again later."}
    assert int(response.headers["retry-after"]) > 0


@pytest.mark.asyncio
async def test_lockout_is_per_email(client: AsyncClient) -> None:
    await register_user(client)
    await register_user(client, "other@example.com")
    for _ in range(5):
        await _login(client, "wrong-password")
    assert (await _login(client, PASSWORD, "other@example.com")).status_code == 200


@pytest.mark.asyncio
async def test_successful_login_clears_failures(client: AsyncClient) -> None:
    await register_user(client)
    for _ in range(4):
        await _login(client, "wrong-password")
    assert (await _login(client, PASSWORD)).status_code == 200
    for _ in range(4):
        assert (await _login(client, "wrong-password")).status_code == 401


@pytest.mark.asyncio
async def test_unknown_emails_are_limited_like_real_ones(client: AsyncClient) -> None:
    for _ in range(5):
        assert (await _login(client, "x", "ghost@example.com")).status_code == 401
    assert (await _login(client, "x", "ghost@example.com")).status_code == 429


@pytest.mark.asyncio
async def test_login_is_limited_per_ip(client: AsyncClient) -> None:
    await register_user(client)
    # Different emails each time, so only the per-IP limit can trigger.
    for i in range(20):
        assert (await _login(client, "x", f"user{i}@example.com")).status_code == 401
    assert (await _login(client, PASSWORD)).status_code == 429


@pytest.mark.asyncio
async def test_register_is_limited_per_ip(client: AsyncClient) -> None:
    for i in range(10):
        await register_user(client, f"user{i}@example.com")
    response = await client.post(
        "/auth/register", json={**REGISTER_PAYLOAD, "email": "one-more@example.com"}
    )
    assert response.status_code == 429

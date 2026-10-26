import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import FORGOT_PASSWORD_MESSAGE
from app.core.security import create_email_verification_token
from app.models.user import User
from tests.conftest import (
    REGISTER_PAYLOAD,
    access_token_issued_ago,
    auth_header,
    register_user,
    user_id,
)
from tests.fakes import FakeEmailSender, link_token

EMAIL = REGISTER_PAYLOAD["email"]
OLD_PASSWORD = REGISTER_PAYLOAD["password"]
NEW_PASSWORD = "brand-new-password"


async def _forgot(client: AsyncClient, email: str = EMAIL) -> None:
    response = await client.post("/auth/forgot-password", json={"email": email})
    assert response.status_code == 202, response.text
    assert response.json() == {"detail": FORGOT_PASSWORD_MESSAGE}


async def _reset(client: AsyncClient, token: str, password: str = NEW_PASSWORD) -> int:
    response = await client.post(
        "/auth/reset-password", json={"token": token, "new_password": password}
    )
    return response.status_code


async def _login(client: AsyncClient, password: str) -> int:
    response = await client.post("/auth/login", json={"email": EMAIL, "password": password})
    return response.status_code


def _reset_email_token(outbox: FakeEmailSender) -> str:
    [message] = [m for m in outbox.to(EMAIL) if "Reset" in m.subject]
    assert "http://frontend.test/reset-password?token=" in message.body
    return link_token(message)


@pytest.mark.asyncio
async def test_forgot_password_emails_a_reset_link(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    await _forgot(client)
    _reset_email_token(outbox)


@pytest.mark.asyncio
async def test_forgot_password_for_unknown_email_looks_the_same(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await _forgot(client, "nobody@example.com")
    assert outbox.sent == []


@pytest.mark.asyncio
async def test_forgot_password_is_case_insensitive(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    await _forgot(client, EMAIL.upper())
    _reset_email_token(outbox)


@pytest.mark.asyncio
async def test_forgot_password_for_inactive_user_sends_nothing(
    client: AsyncClient,
    outbox: FakeEmailSender,
    db_session: AsyncSession,
) -> None:
    await register_user(client)
    await db_session.execute(update(User).values(is_active=False))
    await db_session.commit()
    outbox.sent.clear()

    await _forgot(client)
    assert outbox.sent == []


@pytest.mark.asyncio
async def test_reset_password_changes_the_password(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    await _forgot(client)
    assert await _reset(client, _reset_email_token(outbox)) == 204

    assert await _login(client, NEW_PASSWORD) == 200
    assert await _login(client, OLD_PASSWORD) == 401
    assert any("password was changed" in m.subject for m in outbox.to(EMAIL))


@pytest.mark.asyncio
async def test_reset_link_works_only_once(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    await _forgot(client)
    token = _reset_email_token(outbox)
    assert await _reset(client, token) == 204
    assert await _reset(client, token, "another-password-1") == 400
    assert await _login(client, NEW_PASSWORD) == 200


@pytest.mark.asyncio
async def test_reset_link_dies_when_password_changes_another_way(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    token = await register_user(client)
    await _forgot(client)
    reset_token = _reset_email_token(outbox)
    changed = await client.post(
        "/users/me/password",
        json={"current_password": OLD_PASSWORD, "new_password": "changed-in-settings"},
        headers=auth_header(token),
    )
    assert changed.status_code == 200
    assert await _reset(client, reset_token) == 400


@pytest.mark.asyncio
async def test_reset_signs_out_existing_sessions(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    uid = await user_id(client, await register_user(client))
    earlier_session = access_token_issued_ago(uid, seconds=60)
    assert (await client.get("/auth/me", headers=auth_header(earlier_session))).status_code == 200

    await _forgot(client)
    await _reset(client, _reset_email_token(outbox))
    response = await client.get("/auth/me", headers=auth_header(earlier_session))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reset_marks_email_as_verified(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    await _forgot(client)
    await _reset(client, _reset_email_token(outbox))
    login = await client.post("/auth/login", json={"email": EMAIL, "password": NEW_PASSWORD})
    assert login.json()["user"]["email_verified"] is True


@pytest.mark.asyncio
async def test_reset_lifts_login_lockout(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    for _ in range(5):
        assert await _login(client, "wrong-password") == 401
    assert await _login(client, OLD_PASSWORD) == 429

    await _forgot(client)
    await _reset(client, _reset_email_token(outbox))
    assert await _login(client, NEW_PASSWORD) == 200


@pytest.mark.asyncio
async def test_reset_rejects_bad_tokens(client: AsyncClient) -> None:
    uid = await user_id(client, await register_user(client))
    assert await _reset(client, "garbage") == 400
    # A verification link must not work as a reset link.
    assert await _reset(client, create_email_verification_token(uid, EMAIL)) == 400


@pytest.mark.asyncio
async def test_reset_enforces_password_rules(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    await _forgot(client)
    assert await _reset(client, _reset_email_token(outbox), "short") == 422


@pytest.mark.asyncio
async def test_forgot_password_is_rate_limited_per_email(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    outbox.sent.clear()
    for _ in range(3):
        await _forgot(client)
    response = await client.post("/auth/forgot-password", json={"email": EMAIL})
    assert response.status_code == 429
    assert len(outbox.sent) == 3

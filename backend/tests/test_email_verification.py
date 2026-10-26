from datetime import datetime, timedelta, timezone

import jwt
import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.security import EMAIL_VERIFICATION_TOKEN_TYPE, create_password_reset_token
from tests.conftest import REGISTER_PAYLOAD, auth_header, register_user, user_id
from tests.fakes import FakeEmailSender, link_token

EMAIL = REGISTER_PAYLOAD["email"]


async def _verify(client: AsyncClient, token: str) -> int:
    response = await client.post("/auth/verify-email", json={"token": token})
    return response.status_code


@pytest.mark.asyncio
async def test_register_sends_verification_email(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.json()["user"]["email_verified"] is False

    [message] = outbox.to(EMAIL)
    assert "Verify" in message.subject
    assert "http://frontend.test/verify-email?token=" in message.body


@pytest.mark.asyncio
async def test_verify_email_with_link_token(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    token = await register_user(client)
    response = await client.post(
        "/auth/verify-email", json={"token": link_token(outbox.to(EMAIL)[0])}
    )
    assert response.status_code == 200
    assert response.json()["email_verified"] is True

    me = await client.get("/auth/me", headers=auth_header(token))
    assert me.json()["email_verified"] is True


@pytest.mark.asyncio
async def test_verify_email_twice_is_fine(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    await register_user(client)
    token = link_token(outbox.to(EMAIL)[0])
    assert await _verify(client, token) == 200
    assert await _verify(client, token) == 200


@pytest.mark.asyncio
async def test_verify_email_rejects_garbage(client: AsyncClient) -> None:
    response = await client.post("/auth/verify-email", json={"token": "not-a-token"})
    assert response.status_code == 400
    assert response.json() == {"detail": "This verification link is invalid or has expired"}


@pytest.mark.asyncio
async def test_other_token_types_cannot_verify_email(client: AsyncClient) -> None:
    access_token = await register_user(client)
    uid = await user_id(client, access_token)
    reset_token = create_password_reset_token(uid, EMAIL, "some-hash")
    assert await _verify(client, access_token) == 400
    assert await _verify(client, reset_token) == 400


@pytest.mark.asyncio
async def test_expired_verification_link_is_rejected(client: AsyncClient) -> None:
    uid = await user_id(client, await register_user(client))
    settings = get_settings()
    past = datetime.now(timezone.utc) - timedelta(days=2)
    expired = jwt.encode(
        {
            "sub": uid,
            "email": EMAIL,
            "type": EMAIL_VERIFICATION_TOKEN_TYPE,
            "iat": past,
            "exp": past + timedelta(hours=24),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    assert await _verify(client, expired) == 400


@pytest.mark.asyncio
async def test_link_for_old_email_stops_working_after_email_change(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    token = await register_user(client)
    old_link = link_token(outbox.to(EMAIL)[0])
    changed = await client.patch(
        "/users/me",
        json={"email": "new@example.com", "current_password": REGISTER_PAYLOAD["password"]},
        headers=auth_header(token),
    )
    assert changed.status_code == 200

    assert await _verify(client, old_link) == 400
    assert await _verify(client, link_token(outbox.to("new@example.com")[0])) == 200


@pytest.mark.asyncio
async def test_resend_verification_sends_a_new_link(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    token = await register_user(client)
    response = await client.post("/auth/resend-verification", headers=auth_header(token))
    assert response.status_code == 204
    assert len(outbox.to(EMAIL)) == 2
    assert await _verify(client, link_token(outbox.to(EMAIL)[1])) == 200


@pytest.mark.asyncio
async def test_resend_when_already_verified_returns_409(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    token = await register_user(client)
    await _verify(client, link_token(outbox.to(EMAIL)[0]))
    response = await client.post("/auth/resend-verification", headers=auth_header(token))
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_resend_verification_is_rate_limited(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    token = await register_user(client)
    for _ in range(3):
        response = await client.post("/auth/resend-verification", headers=auth_header(token))
        assert response.status_code == 204
    response = await client.post("/auth/resend-verification", headers=auth_header(token))
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0
    assert len(outbox.to(EMAIL)) == 4  # signup + 3 resends


@pytest.mark.asyncio
async def test_resend_requires_login(client: AsyncClient) -> None:
    response = await client.post("/auth/resend-verification")
    assert response.status_code == 401

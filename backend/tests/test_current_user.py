import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.config import get_settings
from app.core.exceptions import PermissionDeniedError
from app.core.security import create_access_token
from app.models.user import User, UserRole
from tests.conftest import REGISTER_PAYLOAD, auth_header


async def _register(client: AsyncClient) -> str:
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    return response.json()["access_token"]


def _signed_token(payload: dict[str, object], secret: str | None = None) -> str:
    settings = get_settings()
    return jwt.encode(
        payload,
        secret or settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient) -> None:
    token = await _register(client)
    response = await client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["role"] == REGISTER_PAYLOAD["role"]
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_me_with_login_token(client: AsyncClient) -> None:
    await _register(client)
    login = await client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    response = await client.get(
        "/auth/me", headers=auth_header(login.json()["access_token"])
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        _signed_token(
            {"sub": str(uuid.uuid4()), "iat": 0, "exp": 9999999999},
            secret="a-different-secret-that-is-32-bytes-long",
        ),
        _signed_token({"sub": "not-a-uuid", "iat": 0, "exp": 9999999999}),
        _signed_token({"iat": 0, "exp": 9999999999}),
    ],
    ids=["garbage", "wrong-signature", "sub-not-uuid", "missing-sub"],
)
async def test_me_with_invalid_token_returns_401(
    client: AsyncClient,
    token: str,
) -> None:
    response = await client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token"}


@pytest.mark.asyncio
async def test_me_with_expired_token_returns_401(client: AsyncClient) -> None:
    await _register(client)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    token = _signed_token(
        {"sub": str(uuid.uuid4()), "iat": past, "exp": past + timedelta(minutes=1)}
    )
    response = await client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_for_deleted_user_returns_401(client: AsyncClient) -> None:
    token = create_access_token(str(uuid.uuid4()), UserRole.devops_engineer.value)
    response = await client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_for_deactivated_user_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token = await _register(client)
    await db_session.execute(update(User).values(is_active=False))
    await db_session.commit()

    response = await client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_require_roles_allows_matching_role() -> None:
    user = User(role=UserRole.admin)
    checker = require_roles(UserRole.admin, UserRole.devops_engineer)
    assert await checker(user) is user


@pytest.mark.asyncio
async def test_require_roles_rejects_other_roles() -> None:
    user = User(role=UserRole.application_developer)
    with pytest.raises(PermissionDeniedError):
        await require_roles(UserRole.admin)(user)

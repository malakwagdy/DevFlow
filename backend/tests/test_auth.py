from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import LOGIN_FAILURE_MESSAGE
from app.models.company import Company
from app.models.team import Team
from app.models.user import User
from app.services.auth_service import DEFAULT_TEAM_NAME
from tests.conftest import REGISTER_PAYLOAD


def _assert_no_hashed_password(payload: Any) -> None:
    if isinstance(payload, dict):
        assert "hashed_password" not in payload
        for value in payload.values():
            _assert_no_hashed_password(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_hashed_password(item)


# --- register -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["user"]["email"] == REGISTER_PAYLOAD["email"]
    assert body["user"]["full_name"] == REGISTER_PAYLOAD["full_name"]
    assert body["user"]["role"] == REGISTER_PAYLOAD["role"]
    assert body["user"]["is_active"] is True
    assert isinstance(body["user"]["id"], str) and body["user"]["id"]
    _assert_no_hashed_password(body)


@pytest.mark.asyncio
async def test_register_without_company_has_no_company(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    assert response.json()["user"]["company_id"] is None
    assert response.json()["user"]["company_role"] is None
    assert (await db_session.scalars(select(Company))).all() == []
    assert (await db_session.scalars(select(Team))).all() == []


@pytest.mark.asyncio
async def test_register_with_company_creates_owner_company_and_default_team(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = {**REGISTER_PAYLOAD, "company_name": "  Acme  "}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201
    user_body = response.json()["user"]
    assert user_body["company_role"] == "owner"
    assert user_body["company_id"] is not None

    company = (await db_session.scalars(select(Company))).one()
    assert str(company.id) == user_body["company_id"]
    assert company.name == "Acme"

    team = (
        await db_session.scalars(select(Team).options(selectinload(Team.members)))
    ).one()
    assert team.name == DEFAULT_TEAM_NAME
    assert team.company_id == company.id
    assert [member.email for member in team.members] == [REGISTER_PAYLOAD["email"]]


@pytest.mark.asyncio
async def test_register_blank_company_name_is_rejected(client: AsyncClient) -> None:
    payload = {**REGISTER_PAYLOAD, "company_name": "   "}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_too_long_full_name_is_rejected(client: AsyncClient) -> None:
    payload = {**REGISTER_PAYLOAD, "full_name": "x" * 256}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    first = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert first.status_code == 201
    second = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert second.status_code == 409
    assert second.json() == {"detail": "Email already registered"}
    _assert_no_hashed_password(second.json())


@pytest.mark.asyncio
async def test_register_duplicate_email_is_case_insensitive(
    client: AsyncClient,
) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    payload = {**REGISTER_PAYLOAD, "email": "DEV@Example.com"}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_failed_register_with_company_leaves_no_company_behind(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    payload = {**REGISTER_PAYLOAD, "company_name": "Acme"}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert (await db_session.scalars(select(Company))).all() == []


@pytest.mark.asyncio
async def test_register_admin_role_is_rejected(client: AsyncClient) -> None:
    payload = {**REGISTER_PAYLOAD, "email": "admin@example.com", "role": "admin"}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422
    _assert_no_hashed_password(response.json())


# --- login --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success_returns_token(client: AsyncClient) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["user"]["email"] == REGISTER_PAYLOAD["email"]
    _assert_no_hashed_password(body)


@pytest.mark.asyncio
async def test_login_email_is_case_insensitive(client: AsyncClient) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post(
        "/auth/login",
        json={"email": "DEV@EXAMPLE.COM", "password": REGISTER_PAYLOAD["password"]},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": LOGIN_FAILURE_MESSAGE}


@pytest.mark.asyncio
async def test_login_unknown_email_matches_wrong_password_401(
    client: AsyncClient,
) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    wrong_password: Response = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpass"},
    )
    unknown_email: Response = await client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "wrongpass"},
    )
    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert unknown_email.json() == wrong_password.json()
    assert unknown_email.json() == {"detail": LOGIN_FAILURE_MESSAGE}
    _assert_no_hashed_password(wrong_password.json())
    _assert_no_hashed_password(unknown_email.json())


@pytest.mark.asyncio
async def test_login_inactive_user_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    await db_session.execute(update(User).values(is_active=False))
    await db_session.commit()

    response = await client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "User account is inactive"}

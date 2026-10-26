import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.project import Project
from app.models.team import Team
from tests.conftest import (
    REGISTER_PAYLOAD,
    access_token_issued_ago,
    auth_header,
    connect_github,
    register_user,
    user_id,
)
from tests.fakes import FakeEmailSender, FakeGitHubClient, link_token, make_repo

EMAIL = REGISTER_PAYLOAD["email"]
PASSWORD = REGISTER_PAYLOAD["password"]


async def _patch_me(client: AsyncClient, token: str, **payload: object):
    return await client.patch("/users/me", json=payload, headers=auth_header(token))


async def _change_password(client: AsyncClient, token: str, current: str, new: str):
    return await client.post(
        "/users/me/password",
        json={"current_password": current, "new_password": new},
        headers=auth_header(token),
    )


async def _delete_me(client: AsyncClient, token: str, password: str = PASSWORD):
    return await client.request(
        "DELETE", "/users/me", json={"password": password}, headers=auth_header(token)
    )


# --- profile ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_full_name(client: AsyncClient) -> None:
    token = await register_user(client)
    response = await _patch_me(client, token, full_name="  New Name  ")
    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"
    assert response.json()["email"] == EMAIL


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{"full_name": None}, {"full_name": ""}, {"email": None}])
async def test_update_rejects_clearing_fields(client: AsyncClient, payload: dict) -> None:
    token = await register_user(client)
    response = await _patch_me(client, token, **payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_email_requires_current_password(client: AsyncClient) -> None:
    token = await register_user(client)
    response = await _patch_me(client, token, email="new@example.com")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_email_with_wrong_password_returns_403(client: AsyncClient) -> None:
    token = await register_user(client)
    response = await _patch_me(
        client, token, email="new@example.com", current_password="wrong-password"
    )
    assert response.status_code == 403
    me = await client.get("/auth/me", headers=auth_header(token))
    assert me.json()["email"] == EMAIL


@pytest.mark.asyncio
async def test_change_email(client: AsyncClient, outbox: FakeEmailSender) -> None:
    token = await register_user(client)
    await client.post("/auth/verify-email", json={"token": link_token(outbox.to(EMAIL)[0])})
    outbox.sent.clear()

    response = await _patch_me(
        client, token, email="New@Example.com", current_password=PASSWORD
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    assert response.json()["email_verified"] is False

    [verification] = outbox.to("new@example.com")
    assert "Verify" in verification.subject
    [notice] = outbox.to(EMAIL)
    assert "email address was changed" in notice.subject

    login = await client.post(
        "/auth/login", json={"email": "new@example.com", "password": PASSWORD}
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_change_email_to_taken_address_returns_409(client: AsyncClient) -> None:
    await register_user(client, "taken@example.com")
    token = await register_user(client)
    response = await _patch_me(
        client, token, email="taken@example.com", current_password=PASSWORD
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_same_email_is_not_a_change(
    client: AsyncClient,
    outbox: FakeEmailSender,
) -> None:
    token = await register_user(client)
    outbox.sent.clear()
    # current_password is still required by the schema, but no email is sent.
    response = await _patch_me(client, token, email=EMAIL.upper(), current_password=PASSWORD)
    assert response.status_code == 200
    assert outbox.sent == []


# --- password -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, outbox: FakeEmailSender) -> None:
    token = await register_user(client)
    response = await _change_password(client, token, PASSWORD, "new-password-1")
    assert response.status_code == 200

    fresh = response.json()["access_token"]
    assert (await client.get("/auth/me", headers=auth_header(fresh))).status_code == 200
    login = await client.post(
        "/auth/login", json={"email": EMAIL, "password": "new-password-1"}
    )
    assert login.status_code == 200
    assert any("password was changed" in m.subject for m in outbox.to(EMAIL))


@pytest.mark.asyncio
async def test_change_password_signs_out_older_sessions(client: AsyncClient) -> None:
    token = await register_user(client)
    earlier_session = access_token_issued_ago(await user_id(client, token), seconds=60)
    await _change_password(client, token, PASSWORD, "new-password-1")
    response = await client.get("/auth/me", headers=auth_header(earlier_session))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_with_wrong_current_returns_403(client: AsyncClient) -> None:
    token = await register_user(client)
    response = await _change_password(client, token, "wrong-password", "new-password-1")
    assert response.status_code == 403
    assert response.json() == {"detail": "Current password is incorrect"}


@pytest.mark.asyncio
@pytest.mark.parametrize("new_password", [PASSWORD, "short"])
async def test_change_password_rejects_bad_new_password(
    client: AsyncClient,
    new_password: str,
) -> None:
    token = await register_user(client)
    response = await _change_password(client, token, PASSWORD, new_password)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_wrong_current_password_is_rate_limited(client: AsyncClient) -> None:
    token = await register_user(client)
    for _ in range(5):
        response = await _change_password(client, token, "wrong-password", "new-password-1")
        assert response.status_code == 403
    # Locked even with the right password, so a stolen token can't keep guessing.
    response = await _change_password(client, token, PASSWORD, "new-password-1")
    assert response.status_code == 429


# --- delete -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_account(client: AsyncClient) -> None:
    token = await register_user(client)
    response = await _delete_me(client, token)
    assert response.status_code == 204

    assert (await client.get("/auth/me", headers=auth_header(token))).status_code == 401
    login = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert login.status_code == 401
    # The email can be used for a new account.
    await register_user(client)


@pytest.mark.asyncio
async def test_delete_account_with_wrong_password_returns_403(client: AsyncClient) -> None:
    token = await register_user(client)
    response = await _delete_me(client, token, "wrong-password")
    assert response.status_code == 403
    assert (await client.get("/auth/me", headers=auth_header(token))).status_code == 200


@pytest.mark.asyncio
async def test_delete_account_removes_projects_company_and_github(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
    db_session: AsyncSession,
) -> None:
    fake_github.repos = [make_repo(101, "octocat/hello-world")]
    token = await register_user(client, company_name="Acme")
    await connect_github(client, fake_github, token, github_token="gho_to_revoke")
    created = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/hello-world"},
        headers=auth_header(token),
    )
    assert created.status_code == 201

    assert (await _delete_me(client, token)).status_code == 204

    assert fake_github.revoked_tokens == ["gho_to_revoke"]
    assert (await db_session.scalars(select(Project))).all() == []
    assert (await db_session.scalars(select(Company))).all() == []
    assert (await db_session.scalars(select(Team))).all() == []


@pytest.mark.asyncio
async def test_delete_account_works_without_github_configured(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import get_settings

    token = await register_user(client)
    monkeypatch.setattr(get_settings(), "github_client_id", None)
    assert (await _delete_me(client, token)).status_code == 204


@pytest.mark.asyncio
async def test_settings_endpoints_require_login(client: AsyncClient) -> None:
    assert (await client.patch("/users/me", json={"full_name": "X"})).status_code == 401
    response = await client.post(
        "/users/me/password", json={"current_password": "a", "new_password": "bbbbbbbb"}
    )
    assert response.status_code == 401
    response = await client.request("DELETE", "/users/me", json={"password": "a"})
    assert response.status_code == 401

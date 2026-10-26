from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_oauth_state, decrypt_secret
from app.models.github_connection import GitHubConnection
from app.schemas.github import validate_branch_name
from tests.conftest import auth_header, connect_github, redirect_params, register_user
from tests.fakes import FakeGitHubClient, make_repo

# --- starting the connection ----------------------------------------------------


@pytest.mark.asyncio
async def test_connect_requires_login(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    response = await client.get("/github/connect", params={"access": "public"})
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("access", "expected_scope"),
    [("public", "public_repo"), ("private", "repo")],
)
async def test_connect_requests_the_scope_the_user_chose(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
    access: str,
    expected_scope: str,
) -> None:
    token = await register_user(client)
    response = await client.get(
        "/github/connect", params={"access": access}, headers=auth_header(token)
    )
    assert response.status_code == 200
    url = urlparse(response.json()["authorization_url"])
    query = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == (
        "https://github.com/login/oauth/authorize"
    )
    assert query["scope"] == [expected_scope]
    assert query["client_id"] == ["test-client-id"]
    assert query["redirect_uri"] == ["http://testserver/github/callback"]
    assert query["state"][0]


@pytest.mark.asyncio
async def test_connect_rejects_unknown_access_level(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    response = await client.get(
        "/github/connect", params={"access": "everything"}, headers=auth_header(token)
    )
    assert response.status_code == 422


# --- the callback -------------------------------------------------------------


@pytest.mark.asyncio
async def test_callback_connects_account(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    callback = await connect_github(client, fake_github, token, access="private")

    assert callback.status_code == 303
    assert redirect_params(callback) == {"status": "connected", "access": "private"}

    status = await client.get("/github/connection", headers=auth_header(token))
    assert status.status_code == 200
    body = status.json()
    assert body["connected"] is True
    assert body["username"] == "octocat"
    assert body["access"] == "private"
    assert body["connected_at"] is not None
    assert "gho_test_token" not in status.text


@pytest.mark.asyncio
async def test_github_token_is_stored_encrypted(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
    db_session: AsyncSession,
) -> None:
    token = await register_user(client)
    await connect_github(client, fake_github, token, github_token="gho_secret_value")

    connection = (await db_session.scalars(select(GitHubConnection))).one()
    assert "gho_secret_value" not in connection.encrypted_access_token
    assert decrypt_secret(connection.encrypted_access_token) == "gho_secret_value"
    assert connection.scopes == "repo"


@pytest.mark.asyncio
async def test_private_request_with_only_public_scope_granted_is_public(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    callback = await connect_github(
        client, fake_github, token, access="private", granted_scopes={"public_repo"}
    )
    assert redirect_params(callback)["access"] == "public"


@pytest.mark.asyncio
async def test_callback_with_forged_state_does_not_connect(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    fake_github.authorize("code", token="gho_x", scopes={"repo"})
    callback = await client.get(
        "/github/callback", params={"code": "code", "state": "forged"}
    )
    assert redirect_params(callback) == {"status": "error", "reason": "invalid_state"}

    status = await client.get("/github/connection", headers=auth_header(token))
    assert status.json()["connected"] is False


@pytest.mark.asyncio
async def test_login_token_cannot_be_used_as_oauth_state(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    fake_github.authorize("code", token="gho_x", scopes={"repo"})
    callback = await client.get(
        "/github/callback", params={"code": "code", "state": token}
    )
    assert redirect_params(callback)["reason"] == "invalid_state"


@pytest.mark.asyncio
async def test_oauth_state_cannot_be_used_as_login_token(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    me = await client.get("/auth/me", headers=auth_header(token))
    state = create_oauth_state(me.json()["id"], "private")

    response = await client.get("/auth/me", headers=auth_header(state))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_callback_when_user_cancels_on_github(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    me = await client.get("/auth/me", headers=auth_header(token))
    state = create_oauth_state(me.json()["id"], "public")

    callback = await client.get(
        "/github/callback", params={"error": "access_denied", "state": state}
    )
    assert redirect_params(callback) == {"status": "cancelled"}


@pytest.mark.asyncio
async def test_callback_with_rejected_code_redirects_with_error(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    me = await client.get("/auth/me", headers=auth_header(token))
    state = create_oauth_state(me.json()["id"], "public")

    callback = await client.get(
        "/github/callback", params={"code": "expired-code", "state": state}
    )
    assert redirect_params(callback) == {"status": "error", "reason": "github_error"}


# --- status / disconnect ------------------------------------------------------


@pytest.mark.asyncio
async def test_status_when_not_connected(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    response = await client.get("/github/connection", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json() == {
        "connected": False,
        "username": None,
        "access": None,
        "connected_at": None,
    }


@pytest.mark.asyncio
async def test_disconnect_revokes_on_github_and_forgets_token(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
    db_session: AsyncSession,
) -> None:
    token = await register_user(client)
    await connect_github(client, fake_github, token, github_token="gho_to_revoke")

    response = await client.delete("/github/connection", headers=auth_header(token))
    assert response.status_code == 204
    assert fake_github.revoked_tokens == ["gho_to_revoke"]
    assert (await db_session.scalars(select(GitHubConnection))).all() == []


@pytest.mark.asyncio
async def test_disconnect_when_not_connected_returns_409(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    response = await client.delete("/github/connection", headers=auth_header(token))
    assert response.status_code == 409


# --- changing access level ------------------------------------------------------


@pytest.mark.asyncio
async def test_upgrade_public_to_private_replaces_token(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
    db_session: AsyncSession,
) -> None:
    token = await register_user(client)
    await connect_github(
        client, fake_github, token, access="public", github_token="gho_public", code="c1"
    )
    await connect_github(
        client, fake_github, token, access="private", github_token="gho_private", code="c2"
    )

    connection = (await db_session.scalars(select(GitHubConnection))).one()
    assert connection.access.value == "private"
    assert decrypt_secret(connection.encrypted_access_token) == "gho_private"
    assert fake_github.revoked_tokens == []


@pytest.mark.asyncio
async def test_switching_to_public_revokes_the_private_grant(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    await connect_github(client, fake_github, token, access="private", github_token="gho_p")

    response = await client.get(
        "/github/connect", params={"access": "public"}, headers=auth_header(token)
    )
    assert response.status_code == 200
    assert fake_github.revoked_tokens == ["gho_p"]
    status = await client.get("/github/connection", headers=auth_header(token))
    assert status.json()["connected"] is False


# --- repositories -------------------------------------------------------------


@pytest.mark.asyncio
async def test_repos_requires_connection(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    response = await client.get("/github/repos", headers=auth_header(token))
    assert response.status_code == 409
    assert response.json() == {"detail": "GitHub account is not connected"}


@pytest.mark.asyncio
async def test_public_access_lists_only_public_repos(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    fake_github.repos = [
        make_repo(1, "octocat/open-source"),
        make_repo(2, "octocat/secret-app", private=True),
    ]
    token = await register_user(client)
    await connect_github(client, fake_github, token, access="public")

    response = await client.get("/github/repos", headers=auth_header(token))
    assert response.status_code == 200
    names = [repo["full_name"] for repo in response.json()["repositories"]]
    assert names == ["octocat/open-source"]
    assert fake_github.list_visibilities == ["public"]


@pytest.mark.asyncio
async def test_private_access_lists_all_repos(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    fake_github.repos = [
        make_repo(1, "octocat/open-source"),
        make_repo(2, "octocat/secret-app", private=True),
    ]
    token = await register_user(client)
    await connect_github(client, fake_github, token, access="private")

    response = await client.get("/github/repos", headers=auth_header(token))
    body = response.json()
    assert [repo["full_name"] for repo in body["repositories"]] == [
        "octocat/open-source",
        "octocat/secret-app",
    ]
    assert body["repositories"][1]["private"] is True
    assert fake_github.list_visibilities == ["all"]


@pytest.mark.asyncio
async def test_repos_pagination(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    fake_github.repos = [make_repo(i, f"octocat/repo-{i}") for i in range(1, 4)]
    token = await register_user(client)
    await connect_github(client, fake_github, token)

    first = await client.get(
        "/github/repos", params={"per_page": 2}, headers=auth_header(token)
    )
    second = await client.get(
        "/github/repos", params={"per_page": 2, "page": 2}, headers=auth_header(token)
    )
    assert first.json()["has_next"] is True
    assert len(first.json()["repositories"]) == 2
    assert second.json()["has_next"] is False
    assert len(second.json()["repositories"]) == 1


# --- branches -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_branches_lists_repo_branches_with_default(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    fake_github.repos = [make_repo(1, "octocat/hello-world")]
    fake_github.branches = {"octocat/hello-world": ["main", "develop", "release/v2.1"]}
    token = await register_user(client)
    await connect_github(client, fake_github, token)

    response = await client.get(
        "/github/repos/octocat/hello-world/branches", headers=auth_header(token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["default_branch"] == "main"
    assert [branch["name"] for branch in body["branches"]] == [
        "main",
        "develop",
        "release/v2.1",
    ]
    assert body["has_next"] is False


@pytest.mark.asyncio
async def test_branches_pagination(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    fake_github.repos = [make_repo(1, "octocat/hello-world")]
    fake_github.branches = {"octocat/hello-world": ["main", "b1", "b2"]}
    token = await register_user(client)
    await connect_github(client, fake_github, token)

    url = "/github/repos/octocat/hello-world/branches"
    first = await client.get(url, params={"per_page": 2}, headers=auth_header(token))
    second = await client.get(
        url, params={"per_page": 2, "page": 2}, headers=auth_header(token)
    )
    assert [b["name"] for b in first.json()["branches"]] == ["main", "b1"]
    assert first.json()["has_next"] is True
    assert [b["name"] for b in second.json()["branches"]] == ["b2"]
    assert second.json()["has_next"] is False


@pytest.mark.asyncio
async def test_branches_requires_connection(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    response = await client.get(
        "/github/repos/octocat/hello-world/branches", headers=auth_header(token)
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_branches_of_unknown_repo_returns_422(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    await connect_github(client, fake_github, token)
    response = await client.get(
        "/github/repos/octocat/missing/branches", headers=auth_header(token)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_public_access_cannot_list_private_repo_branches(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    fake_github.repos = [make_repo(2, "octocat/secret-app", private=True)]
    token = await register_user(client)
    await connect_github(client, fake_github, token, access="public")
    response = await client.get(
        "/github/repos/octocat/secret-app/branches", headers=auth_header(token)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["octocat/..", "-bad/repo", "octocat/re%20po"])
async def test_branches_rejects_malformed_repo_names(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
    path: str,
) -> None:
    token = await register_user(client)
    await connect_github(client, fake_github, token)
    response = await client.get(f"/github/repos/{path}/branches", headers=auth_header(token))
    # 404 when the URL no longer matches the route at all, 422 when a part is invalid.
    assert response.status_code in (404, 422)


@pytest.mark.parametrize(
    "name", ["main", "release/v2.1", "feature/login-page", "v1.0", "user+fix"]
)
def test_valid_branch_names(name: str) -> None:
    assert validate_branch_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        "../main",
        "a..b",
        "/main",
        "main/",
        "a//b",
        "-main",
        ".hidden",
        "a/.b",
        "x.lock",
        "has space",
        "a~b",
        "a^b",
        "a:b",
        "a\\b",
        "a" * 256,
    ],
)
def test_invalid_branch_names(name: str) -> None:
    with pytest.raises(ValueError):
        validate_branch_name(name)


@pytest.mark.asyncio
async def test_token_revoked_on_github_asks_user_to_reconnect(
    client: AsyncClient,
    fake_github: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    await connect_github(client, fake_github, token, github_token="gho_revoked")
    fake_github.invalid_tokens.add("gho_revoked")

    response = await client.get("/github/repos", headers=auth_header(token))
    assert response.status_code == 409
    assert "reconnect" in response.json()["detail"]
    status = await client.get("/github/connection", headers=auth_header(token))
    assert status.json()["connected"] is False


@pytest.mark.asyncio
async def test_github_endpoints_return_503_when_not_configured(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import get_settings

    access_token = await register_user(client)
    monkeypatch.setattr(get_settings(), "github_client_id", None)
    response = await client.get(
        "/github/connect", params={"access": "public"}, headers=auth_header(access_token)
    )
    assert response.status_code == 503

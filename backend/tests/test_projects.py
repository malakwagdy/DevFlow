import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team, user_teams
from app.models.user import User
from tests.conftest import auth_header, connect_github, register_user
from tests.fakes import FakeGitHubClient, make_repo

PUBLIC_REPO = make_repo(101, "octocat/hello-world", description="My first repo")
PRIVATE_REPO = make_repo(202, "octocat/secret-app", private=True)


@pytest.fixture
def repos(fake_github: FakeGitHubClient) -> FakeGitHubClient:
    fake_github.repos = [PUBLIC_REPO, PRIVATE_REPO]
    return fake_github


async def _connected_user(
    client: AsyncClient,
    fake: FakeGitHubClient,
    *,
    email: str = "dev@example.com",
    access: str = "private",
    **register_overrides: str,
) -> str:
    token = await register_user(client, email, **register_overrides)
    await connect_github(
        client, fake, token, access=access, github_token=f"gho_{email}", code=email
    )
    return token


async def _create(client: AsyncClient, token: str, **payload: object) -> dict:
    response = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/hello-world", **payload},
        headers=auth_header(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


# --- create -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_project_defaults_to_repo_details(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token)

    assert project["name"] == "hello-world"
    assert project["description"] == "My first repo"
    assert project["repo_full_name"] == "octocat/hello-world"
    assert project["repo_url"] == "https://github.com/octocat/hello-world"
    assert project["default_branch"] == "main"
    assert project["branch"] == "main"
    assert project["is_private"] is False
    assert project["team_id"] is None
    me = await client.get("/auth/me", headers=auth_header(token))
    assert project["owner_id"] == me.json()["id"]


@pytest.mark.asyncio
async def test_create_project_with_custom_name_and_description(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token, name="Website", description=None)
    assert project["name"] == "Website"
    assert project["description"] is None


@pytest.mark.asyncio
async def test_create_project_with_chosen_branch(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    repos.branches = {"octocat/hello-world": ["main", "release/v2.1"]}
    token = await _connected_user(client, repos)
    project = await _create(client, token, branch="release/v2.1")
    assert project["branch"] == "release/v2.1"
    assert project["default_branch"] == "main"


@pytest.mark.asyncio
async def test_create_project_with_unknown_branch_returns_422(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    response = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/hello-world", "branch": "does-not-exist"},
        headers=auth_header(token),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Branch not found in this repository"}
    listed = await client.get("/projects", headers=auth_header(token))
    assert listed.json() == []


@pytest.mark.asyncio
async def test_create_project_rejects_invalid_branch_name(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    response = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/hello-world", "branch": "../../etc"},
        headers=auth_header(token),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_requires_github_connection(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    response = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/hello-world"},
        headers=auth_header(token),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_project_requires_login(client: AsyncClient) -> None:
    response = await client.post("/projects", json={"repo_full_name": "a/b"})
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "repo_full_name",
    ["no-slash", "a/b/c", "octocat/..", "../etc", "-bad/name", "owner/name?x=1"],
)
async def test_create_project_rejects_malformed_repo_names(
    client: AsyncClient,
    repos: FakeGitHubClient,
    repo_full_name: str,
) -> None:
    token = await _connected_user(client, repos)
    response = await client.post(
        "/projects",
        json={"repo_full_name": repo_full_name},
        headers=auth_header(token),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_for_unknown_repo(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    response = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/does-not-exist"},
        headers=auth_header(token),
    )
    assert response.status_code == 422
    assert "access" in response.json()["detail"]


@pytest.mark.asyncio
async def test_public_only_user_cannot_create_from_private_repo(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos, access="public")
    response = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/secret-app"},
        headers=auth_header(token),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_private_access_user_can_create_from_private_repo(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos, access="private")
    project = await _create(client, token, repo_full_name="octocat/secret-app")
    assert project["is_private"] is True


@pytest.mark.asyncio
async def test_duplicate_project_for_same_repo_returns_409(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    await _create(client, token)
    response = await client.post(
        "/projects",
        json={"repo_full_name": "octocat/hello-world"},
        headers=auth_header(token),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_company_owner_project_goes_to_default_team(
    client: AsyncClient,
    repos: FakeGitHubClient,
    db_session: AsyncSession,
) -> None:
    token = await _connected_user(client, repos, company_name="Acme")
    project = await _create(client, token)

    team = (await db_session.scalars(select(Team))).one()
    assert project["team_id"] == str(team.id)


# --- read / visibility ----------------------------------------------------------


@pytest.mark.asyncio
async def test_users_only_see_their_own_projects(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    alice = await _connected_user(client, repos, email="alice@example.com")
    bob = await _connected_user(client, repos, email="bob@example.com")
    alice_project = await _create(client, alice)

    alice_list = await client.get("/projects", headers=auth_header(alice))
    bob_list = await client.get("/projects", headers=auth_header(bob))
    assert [p["id"] for p in alice_list.json()] == [alice_project["id"]]
    assert bob_list.json() == []

    bob_get = await client.get(
        f"/projects/{alice_project['id']}", headers=auth_header(bob)
    )
    assert bob_get.status_code == 404


@pytest.mark.asyncio
async def test_get_unknown_project_returns_404(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await register_user(client)
    response = await client.get(f"/projects/{uuid.uuid4()}", headers=auth_header(token))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_teammate_can_view_but_not_change_team_project(
    client: AsyncClient,
    repos: FakeGitHubClient,
    db_session: AsyncSession,
) -> None:
    owner = await _connected_user(
        client, repos, email="owner@example.com", company_name="Acme"
    )
    project = await _create(client, owner)

    # No invite flow yet: put a second user into the team directly.
    teammate = await register_user(client, "mate@example.com")
    mate_id = await db_session.scalar(
        select(User.id).where(User.email == "mate@example.com")
    )
    await db_session.execute(
        insert(user_teams).values(user_id=mate_id, team_id=uuid.UUID(project["team_id"]))
    )
    await db_session.commit()

    listed = await client.get("/projects", headers=auth_header(teammate))
    assert [p["id"] for p in listed.json()] == [project["id"]]

    patch = await client.patch(
        f"/projects/{project['id']}",
        json={"name": "hijacked"},
        headers=auth_header(teammate),
    )
    delete = await client.delete(
        f"/projects/{project['id']}", headers=auth_header(teammate)
    )
    assert patch.status_code == 403
    assert delete.status_code == 403


# --- update / delete -------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_can_update_project(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token)

    response = await client.patch(
        f"/projects/{project['id']}",
        json={"name": "Renamed", "description": None},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert response.json()["description"] is None
    assert response.json()["repo_full_name"] == "octocat/hello-world"


@pytest.mark.asyncio
async def test_update_only_changes_fields_sent(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token)

    response = await client.patch(
        f"/projects/{project['id']}",
        json={"name": "Renamed"},
        headers=auth_header(token),
    )
    assert response.json()["description"] == "My first repo"


@pytest.mark.asyncio
async def test_update_cannot_clear_name(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token)
    response = await client.patch(
        f"/projects/{project['id']}",
        json={"name": None},
        headers=auth_header(token),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_owner_can_change_branch(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    repos.branches = {"octocat/hello-world": ["main", "develop"]}
    token = await _connected_user(client, repos)
    project = await _create(client, token)

    response = await client.patch(
        f"/projects/{project['id']}",
        json={"branch": "develop"},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["branch"] == "develop"


@pytest.mark.asyncio
async def test_change_to_unknown_branch_returns_422(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token)

    response = await client.patch(
        f"/projects/{project['id']}",
        json={"branch": "nope"},
        headers=auth_header(token),
    )
    assert response.status_code == 422
    unchanged = await client.get(f"/projects/{project['id']}", headers=auth_header(token))
    assert unchanged.json()["branch"] == "main"


@pytest.mark.asyncio
async def test_update_cannot_clear_branch(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token)
    response = await client.patch(
        f"/projects/{project['id']}",
        json={"branch": None},
        headers=auth_header(token),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_owner_can_delete_project(
    client: AsyncClient,
    repos: FakeGitHubClient,
) -> None:
    token = await _connected_user(client, repos)
    project = await _create(client, token)

    response = await client.delete(
        f"/projects/{project['id']}", headers=auth_header(token)
    )
    assert response.status_code == 204
    gone = await client.get(f"/projects/{project['id']}", headers=auth_header(token))
    assert gone.status_code == 404

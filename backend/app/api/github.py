from fastapi import APIRouter, Query, Response, status
from fastapi.responses import RedirectResponse

from app.api.dependencies import CurrentUserDep, GitHubServiceDep
from app.models.github_connection import GitHubAccess
from app.schemas.github import (
    GitHubAuthorizationUrl,
    GitHubConnectionStatus,
    GitHubRepository,
    GitHubRepositoryPage,
)

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/connect", response_model=GitHubAuthorizationUrl)
async def connect(
    current_user: CurrentUserDep,
    github: GitHubServiceDep,
    access: GitHubAccess = Query(
        description="`public`: public repos only. `private`: public and private repos.",
    ),
) -> GitHubAuthorizationUrl:
    """Start linking GitHub. The frontend then sends the browser to `authorization_url`.

    Returned as JSON (not a redirect) because the browser can't attach our
    Authorization header when navigating.
    """
    url = await github.authorization_url(current_user, access)
    return GitHubAuthorizationUrl(authorization_url=url)


@router.get("/callback", include_in_schema=False)
async def callback(
    github: GitHubServiceDep,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """GitHub redirects the browser here; we bounce it back to the frontend."""
    target = await github.complete_authorization(code=code, state=state, error=error)
    return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/connection", response_model=GitHubConnectionStatus)
async def connection_status(
    current_user: CurrentUserDep,
    github: GitHubServiceDep,
) -> GitHubConnectionStatus:
    connection = await github.get_connection(current_user)
    if connection is None:
        return GitHubConnectionStatus(connected=False)
    return GitHubConnectionStatus(
        connected=True,
        username=connection.github_login,
        access=connection.access,
        connected_at=connection.created_at,
    )


@router.delete("/connection", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    current_user: CurrentUserDep,
    github: GitHubServiceDep,
) -> Response:
    """Revoke DevFlow's access on GitHub and delete the stored token."""
    await github.disconnect(current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/repos", response_model=GitHubRepositoryPage)
async def list_repositories(
    current_user: CurrentUserDep,
    github: GitHubServiceDep,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
) -> GitHubRepositoryPage:
    result = await github.list_repositories(current_user, page=page, per_page=per_page)
    return GitHubRepositoryPage(
        repositories=[GitHubRepository.model_validate(repo) for repo in result.repos],
        page=page,
        per_page=per_page,
        has_next=result.has_next,
    )

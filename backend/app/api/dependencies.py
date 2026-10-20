import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.exceptions import (
    GitHubNotConfiguredError,
    InactiveUserError,
    InvalidTokenError,
    NotAuthenticatedError,
    PermissionDeniedError,
)
from app.core.security import decode_access_token
from app.integrations.github import GitHubClient
from app.models.user import User, UserRole
from app.repositories.github_connection_repository import GitHubConnectionRepository
from app.repositories.user_repository import UserRepository
from app.services.github_service import GitHubService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# auto_error=False so a missing header goes through our own 401 error format.
# Also adds the "Authorize" button (paste the access_token) to /docs.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> User:
    if credentials is None:
        raise NotAuthenticatedError()

    payload = decode_access_token(credentials.credentials)
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidTokenError() from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise InvalidTokenError()
    if not user.is_active:
        raise InactiveUserError()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Dependency factory: `Depends(require_roles(UserRole.admin))`.

    Checks the role stored in the database, not the one in the token, so a role
    change takes effect immediately.
    """

    async def checker(user: CurrentUserDep) -> User:
        if user.role not in roles:
            raise PermissionDeniedError()
        return user

    return checker


def get_github_client() -> GitHubClient:
    """Overridden with a fake in tests."""
    settings = get_settings()
    client_id = settings.github_client_id
    client_secret = settings.github_client_secret
    if not (client_id and client_secret and settings.github_token_encryption_key):
        raise GitHubNotConfiguredError()
    return GitHubClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=settings.github_redirect_uri,
    )


def get_github_service(
    session: SessionDep,
    client: Annotated[GitHubClient, Depends(get_github_client)],
) -> GitHubService:
    return GitHubService(
        GitHubConnectionRepository(session),
        UserRepository(session),
        client,
    )


GitHubServiceDep = Annotated[GitHubService, Depends(get_github_service)]

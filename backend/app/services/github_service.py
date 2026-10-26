import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import TypeVar
from urllib.parse import urlencode

from app.core.config import get_settings
from app.core.exceptions import (
    BranchNotFoundError,
    GitHubNotConnectedError,
    GitHubReauthorizationRequiredError,
    GitHubUnavailableError,
    InvalidTokenError,
    RepositoryNotAccessibleError,
)
from app.core.security import (
    SecretDecryptionError,
    create_oauth_state,
    decode_oauth_state,
    decrypt_secret,
    encrypt_secret,
)
from app.integrations.github import (
    GitHubAuthError,
    GitHubBranchPage,
    GitHubClient,
    GitHubError,
    GitHubRepo,
    GitHubRepoPage,
)
from app.models.github_connection import GitHubAccess, GitHubConnection
from app.models.user import User
from app.repositories.github_connection_repository import GitHubConnectionRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

T = TypeVar("T")

SCOPE_FOR_ACCESS = {
    GitHubAccess.public: "public_repo",
    GitHubAccess.private: "repo",
}
# Frontend page the browser lands on after GitHub, with ?status=connected|cancelled|error
FRONTEND_RESULT_PATH = "/integrations/github"


class GitHubService:
    """Linking a DevFlow user to GitHub, and acting on GitHub as that user."""

    def __init__(
        self,
        connections: GitHubConnectionRepository,
        users: UserRepository,
        client: GitHubClient,
    ) -> None:
        self._connections = connections
        self._users = users
        self._client = client

    # --- connecting -------------------------------------------------------------

    async def authorization_url(self, user: User, access: GitHubAccess) -> str:
        existing = await self._connections.get_by_user_id(user.id)
        if (
            existing is not None
            and existing.access is GitHubAccess.private
            and access is GitHubAccess.public
        ):
            # A GitHub token's scope can't be narrowed, so downgrading means
            # revoking the private grant and having the user consent again.
            await self._revoke_and_delete(existing)

        state = create_oauth_state(str(user.id), access.value)
        return self._client.authorization_url(scope=SCOPE_FOR_ACCESS[access], state=state)

    async def complete_authorization(
        self,
        *,
        code: str | None,
        state: str | None,
        error: str | None,
    ) -> str:
        """Handle GitHub's redirect; returns the frontend URL to send the browser to."""
        try:
            payload = decode_oauth_state(state or "")
            user_id = uuid.UUID(payload["sub"])
            requested = GitHubAccess(payload["access"])
        except (InvalidTokenError, KeyError, ValueError):
            return self._frontend_url(status="error", reason="invalid_state")

        if error is not None:
            # Typically "access_denied": the user clicked Cancel on GitHub.
            return self._frontend_url(status="cancelled")

        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            return self._frontend_url(status="error", reason="invalid_state")
        if not code:
            return self._frontend_url(status="error", reason="missing_code")

        try:
            token = await self._client.exchange_code(code)
            github_user = await self._client.get_user(token.access_token)
        except GitHubError:
            logger.warning("GitHub OAuth exchange failed for user %s", user.id, exc_info=True)
            return self._frontend_url(status="error", reason="github_error")

        # Trust what GitHub granted, not what we asked for.
        access = (
            GitHubAccess.private
            if requested is GitHubAccess.private and "repo" in token.scopes
            else GitHubAccess.public
        )
        connection = await self._connections.get_by_user_id(user.id) or GitHubConnection(
            user_id=user.id
        )
        connection.github_user_id = github_user.id
        connection.github_login = github_user.login
        connection.encrypted_access_token = encrypt_secret(token.access_token)
        connection.scopes = ",".join(sorted(token.scopes))
        connection.access = access
        await self._connections.save(connection)

        return self._frontend_url(status="connected", access=access.value)

    async def get_connection(self, user: User) -> GitHubConnection | None:
        return await self._connections.get_by_user_id(user.id)

    async def disconnect(self, user: User) -> None:
        connection = await self._require_connection(user)
        await self._revoke_and_delete(connection)

    async def disconnect_if_connected(self, user: User) -> None:
        """For account deletion: revoke on GitHub too, not just drop our copy."""
        connection = await self._connections.get_by_user_id(user.id)
        if connection is not None:
            await self._revoke_and_delete(connection)

    # --- acting as the user on GitHub ---------------------------------------------

    async def list_repositories(
        self,
        user: User,
        *,
        page: int,
        per_page: int,
    ) -> GitHubRepoPage:
        connection = await self._require_connection(user)
        # Filter explicitly too, so a public-only user can never see private repos.
        visibility = "all" if connection.access is GitHubAccess.private else "public"
        return await self._with_token(
            connection,
            lambda token: self._client.list_repos(
                token, visibility=visibility, page=page, per_page=per_page
            ),
        )

    async def get_repository(self, user: User, full_name: str) -> GitHubRepo:
        connection = await self._require_connection(user)
        repo = await self._with_token(
            connection,
            lambda token: self._client.get_repo(token, full_name),
        )
        if repo is None or (repo.private and connection.access is GitHubAccess.public):
            raise RepositoryNotAccessibleError()
        return repo

    async def list_branches(
        self,
        user: User,
        full_name: str,
        *,
        page: int,
        per_page: int,
    ) -> tuple[GitHubRepo, GitHubBranchPage]:
        """The repo (for its default branch) and one page of its branches."""
        # Goes through get_repository so the public/private access rule applies.
        repo = await self.get_repository(user, full_name)
        connection = await self._require_connection(user)
        branches = await self._with_token(
            connection,
            lambda token: self._client.list_branches(
                token, repo.full_name, page=page, per_page=per_page
            ),
        )
        if branches is None:
            raise RepositoryNotAccessibleError()
        return repo, branches

    async def ensure_branch_exists(self, user: User, repo: GitHubRepo, branch: str) -> None:
        """`repo` must come from get_repository, which already checked access."""
        if branch == repo.default_branch:
            return  # GitHub just told us it exists; skip the extra call.
        connection = await self._require_connection(user)
        found = await self._with_token(
            connection,
            lambda token: self._client.get_branch(token, repo.full_name, branch),
        )
        if found is None:
            raise BranchNotFoundError()

    # --- helpers ----------------------------------------------------------------

    async def _require_connection(self, user: User) -> GitHubConnection:
        connection = await self._connections.get_by_user_id(user.id)
        if connection is None:
            raise GitHubNotConnectedError()
        return connection

    async def _with_token(
        self,
        connection: GitHubConnection,
        call: Callable[[str], Awaitable[T]],
    ) -> T:
        try:
            token = decrypt_secret(connection.encrypted_access_token)
        except SecretDecryptionError:
            logger.error("Stored GitHub token for user %s can't be decrypted", connection.user_id)
            await self._connections.delete(connection)
            raise GitHubReauthorizationRequiredError() from None

        try:
            return await call(token)
        except GitHubAuthError:
            # Revoked from GitHub's settings page, or expired: forget it.
            await self._connections.delete(connection)
            raise GitHubReauthorizationRequiredError() from None
        except GitHubError as exc:
            logger.warning("GitHub API call failed", exc_info=True)
            raise GitHubUnavailableError() from exc

    async def _revoke_and_delete(self, connection: GitHubConnection) -> None:
        try:
            await self._client.revoke_grant(decrypt_secret(connection.encrypted_access_token))
        except (SecretDecryptionError, GitHubError):
            # Still delete locally; the user can also revoke from GitHub's settings.
            logger.warning(
                "Could not revoke GitHub grant for user %s", connection.user_id, exc_info=True
            )
        await self._connections.delete(connection)

    @staticmethod
    def _frontend_url(**params: str) -> str:
        base = get_settings().frontend_url.rstrip("/")
        return f"{base}{FRONTEND_RESULT_PATH}?{urlencode(params)}"

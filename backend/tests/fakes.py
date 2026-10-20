from datetime import datetime, timezone

from app.integrations.github import (
    GitHubAuthError,
    GitHubClient,
    GitHubOAuthError,
    GitHubRepo,
    GitHubRepoPage,
    GitHubToken,
    GitHubUser,
)


def make_repo(
    repo_id: int,
    full_name: str,
    *,
    private: bool = False,
    description: str | None = None,
) -> GitHubRepo:
    return GitHubRepo(
        id=repo_id,
        name=full_name.split("/")[1],
        full_name=full_name,
        private=private,
        html_url=f"https://github.com/{full_name}",
        default_branch="main",
        description=description,
        language="Python",
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class FakeGitHubClient(GitHubClient):
    """In-memory GitHub that mimics scope rules: a token without `repo` can't
    see private repositories."""

    def __init__(self) -> None:
        super().__init__(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://testserver/github/callback",
        )
        self._codes: dict[str, GitHubToken] = {}
        self._users: dict[str, GitHubUser] = {}
        self._token_scopes: dict[str, frozenset[str]] = {}
        self.repos: list[GitHubRepo] = []
        self.invalid_tokens: set[str] = set()
        self.revoked_tokens: list[str] = []
        self.list_visibilities: list[str] = []

    def authorize(
        self,
        code: str,
        *,
        token: str,
        scopes: set[str],
        login: str = "octocat",
        github_user_id: int = 583231,
    ) -> None:
        """Pretend the user approved on GitHub, which will redirect with `code`."""
        self._codes[code] = GitHubToken(access_token=token, scopes=frozenset(scopes))
        self._users[token] = GitHubUser(id=github_user_id, login=login)
        self._token_scopes[token] = frozenset(scopes)

    async def exchange_code(self, code: str) -> GitHubToken:
        if code not in self._codes:
            raise GitHubOAuthError("bad_verification_code")
        return self._codes.pop(code)  # codes are single-use, like on GitHub

    async def get_user(self, token: str) -> GitHubUser:
        self._check(token)
        return self._users[token]

    async def list_repos(
        self,
        token: str,
        *,
        visibility: str,
        page: int,
        per_page: int,
    ) -> GitHubRepoPage:
        self._check(token)
        self.list_visibilities.append(visibility)
        visible = [
            repo
            for repo in self.repos
            if (visibility == "all" or not repo.private) and self._can_see(token, repo)
        ]
        start = (page - 1) * per_page
        return GitHubRepoPage(
            repos=visible[start : start + per_page],
            has_next=len(visible) > start + per_page,
        )

    async def get_repo(self, token: str, full_name: str) -> GitHubRepo | None:
        self._check(token)
        for repo in self.repos:
            if repo.full_name.lower() == full_name.lower() and self._can_see(token, repo):
                return repo
        return None

    async def revoke_grant(self, token: str) -> None:
        self.revoked_tokens.append(token)

    def _check(self, token: str) -> None:
        if token in self.invalid_tokens:
            raise GitHubAuthError()

    def _can_see(self, token: str, repo: GitHubRepo) -> bool:
        return not repo.private or "repo" in self._token_scopes.get(token, frozenset())

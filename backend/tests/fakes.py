import re
from datetime import datetime, timezone
from urllib.parse import unquote

from app.integrations.email import EmailMessage, EmailSender
from app.integrations.github import (
    GitHubAuthError,
    GitHubBranch,
    GitHubBranchPage,
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
        # Branch names per repo full_name; repos not listed have only their default branch.
        self.branches: dict[str, list[str]] = {}
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

    async def list_branches(
        self,
        token: str,
        full_name: str,
        *,
        page: int,
        per_page: int,
    ) -> GitHubBranchPage | None:
        repo = await self.get_repo(token, full_name)
        if repo is None:
            return None
        names = self._branch_names(repo)
        start = (page - 1) * per_page
        return GitHubBranchPage(
            branches=[
                GitHubBranch(name=name, protected=name == repo.default_branch)
                for name in names[start : start + per_page]
            ],
            has_next=len(names) > start + per_page,
        )

    async def get_branch(self, token: str, full_name: str, branch: str) -> GitHubBranch | None:
        repo = await self.get_repo(token, full_name)
        if repo is None or branch not in self._branch_names(repo):
            return None
        return GitHubBranch(name=branch, protected=branch == repo.default_branch)

    async def revoke_grant(self, token: str) -> None:
        self.revoked_tokens.append(token)

    def _check(self, token: str) -> None:
        if token in self.invalid_tokens:
            raise GitHubAuthError()

    def _branch_names(self, repo: GitHubRepo) -> list[str]:
        return self.branches.get(repo.full_name, [repo.default_branch])

    def _can_see(self, token: str, repo: GitHubRepo) -> bool:
        return not repo.private or "repo" in self._token_scopes.get(token, frozenset())


class FakeEmailSender(EmailSender):
    """Keeps sent emails in memory instead of sending them."""

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        self.sent.append(message)

    def to(self, address: str) -> list[EmailMessage]:
        return [message for message in self.sent if message.to == address]


def link_token(message: EmailMessage) -> str:
    """The `token` query parameter of the link in an email body."""
    match = re.search(r"[?&]token=([^\s&]+)", message.body)
    assert match, f"no link token in email {message.subject!r}"
    return unquote(match.group(1))

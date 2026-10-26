import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.github_connection import GitHubAccess

# Strict because these are interpolated into GitHub API URLs.
GITHUB_OWNER_PATTERN = r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$"
GITHUB_REPO_NAME_PATTERN = r"^[A-Za-z0-9._-]{1,100}$"
# A safe subset of git's ref-name rules; covers names like "release/v2.1".
_BRANCH_CHARS = re.compile(r"^[A-Za-z0-9._/+-]{1,255}$")


def validate_branch_name(value: str) -> str:
    """Raises ValueError for names git would reject or that could escape the URL path."""
    if (
        not _BRANCH_CHARS.match(value)
        or value.startswith(("/", "-", "."))
        or value.endswith(("/", ".", ".lock"))
        or ".." in value
        or "//" in value
        or "/." in value
    ):
        raise ValueError("Invalid branch name")
    return value


class GitHubAuthorizationUrl(BaseModel):
    """The frontend sends the browser here (window.location = authorization_url)."""

    authorization_url: str


class GitHubConnectionStatus(BaseModel):
    connected: bool
    username: str | None = None
    access: GitHubAccess | None = None
    connected_at: datetime | None = None


class GitHubRepository(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    default_branch: str
    description: str | None
    language: str | None
    updated_at: datetime | None


class GitHubRepositoryPage(BaseModel):
    repositories: list[GitHubRepository]
    page: int
    per_page: int
    has_next: bool


class GitHubBranch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    protected: bool


class GitHubBranchPage(BaseModel):
    # GitHub's branch list doesn't flag the default one, so it's sent alongside.
    default_branch: str
    branches: list[GitHubBranch]
    page: int
    per_page: int
    has_next: bool

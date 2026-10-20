from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.github_connection import GitHubAccess


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

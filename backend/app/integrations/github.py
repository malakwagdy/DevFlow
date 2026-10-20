"""Thin async client for the GitHub OAuth flow and REST API.

Raises GitHubError subclasses only; mapping them to HTTP responses is the
service layer's job. Tokens are never logged.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx

GITHUB_OAUTH_URL = "https://github.com/login/oauth"
GITHUB_API_URL = "https://api.github.com"
_TIMEOUT = httpx.Timeout(10.0)


class GitHubError(Exception):
    """GitHub was unreachable or answered unexpectedly."""


class GitHubAuthError(GitHubError):
    """The user's token is invalid, expired or revoked (HTTP 401)."""


class GitHubOAuthError(GitHubError):
    """The OAuth code exchange was rejected (e.g. code expired or reused)."""


@dataclass(frozen=True)
class GitHubToken:
    access_token: str
    scopes: frozenset[str]


@dataclass(frozen=True)
class GitHubUser:
    id: int
    login: str


@dataclass(frozen=True)
class GitHubRepo:
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    default_branch: str
    description: str | None
    language: str | None
    updated_at: datetime | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "GitHubRepo":
        updated_at = data.get("updated_at")
        return cls(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            private=data["private"],
            html_url=data["html_url"],
            default_branch=data.get("default_branch") or "main",
            description=data.get("description"),
            language=data.get("language"),
            updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
        )


@dataclass(frozen=True)
class GitHubRepoPage:
    repos: list[GitHubRepo]
    has_next: bool


class GitHubClient:
    def __init__(self, *, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def authorization_url(self, *, scope: str, state: str) -> str:
        query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "scope": scope,
                "state": state,
            }
        )
        return f"{GITHUB_OAUTH_URL}/authorize?{query}"

    async def exchange_code(self, code: str) -> GitHubToken:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.post(
                    f"{GITHUB_OAUTH_URL}/access_token",
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "redirect_uri": self._redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                )
        except httpx.HTTPError as exc:
            raise GitHubError("Could not reach GitHub") from exc

        if response.status_code != 200:
            raise GitHubError(f"Token exchange failed with HTTP {response.status_code}")
        data = response.json()
        # GitHub reports a bad/expired code as HTTP 200 with an "error" field.
        if "error" in data or "access_token" not in data:
            raise GitHubOAuthError(data.get("error", "missing_access_token"))
        scopes = frozenset(s for s in data.get("scope", "").split(",") if s)
        return GitHubToken(access_token=data["access_token"], scopes=scopes)

    async def get_user(self, token: str) -> GitHubUser:
        response = await self._api("GET", "/user", token=token)
        self._expect_ok(response)
        data = response.json()
        return GitHubUser(id=data["id"], login=data["login"])

    async def list_repos(
        self,
        token: str,
        *,
        visibility: str,
        page: int,
        per_page: int,
    ) -> GitHubRepoPage:
        response = await self._api(
            "GET",
            "/user/repos",
            token=token,
            params={
                "visibility": visibility,
                "sort": "updated",
                "page": page,
                "per_page": per_page,
            },
        )
        self._expect_ok(response)
        return GitHubRepoPage(
            repos=[GitHubRepo.from_api(item) for item in response.json()],
            has_next="next" in response.links,
        )

    async def get_repo(self, token: str, full_name: str) -> GitHubRepo | None:
        """None if the repo doesn't exist or the token can't see it."""
        response = await self._api("GET", f"/repos/{full_name}", token=token)
        if response.status_code == 404:
            return None
        self._expect_ok(response)
        return GitHubRepo.from_api(response.json())

    async def revoke_grant(self, token: str) -> None:
        """Revoke DevFlow's whole authorization for this user (all their tokens)."""
        response = await self._api(
            "DELETE",
            f"/applications/{self._client_id}/grant",
            auth=(self._client_id, self._client_secret),
            json={"access_token": token},
        )
        # 404/422: already revoked on GitHub's side, which is what we wanted anyway.
        if response.status_code not in (204, 404, 422):
            raise GitHubError(f"Grant revocation failed with HTTP {response.status_code}")

    async def _api(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DevFlow",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with httpx.AsyncClient(base_url=GITHUB_API_URL, timeout=_TIMEOUT) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise GitHubError("Could not reach GitHub") from exc
        if response.status_code == 401 and token is not None:
            raise GitHubAuthError()
        return response

    @staticmethod
    def _expect_ok(response: httpx.Response) -> None:
        if response.status_code != 200:
            raise GitHubError(f"GitHub API returned HTTP {response.status_code}")

import os
from collections.abc import AsyncIterator

# Always point tests at a dedicated database: the fixture drops every table.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://devflow:devflow@localhost:5432/devflow_test",
)
os.environ.setdefault("JWT_SECRET", "test-only-secret-key-at-least-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
# Fixed test values, so a real GitHub app configured in .env is never used.
os.environ["FRONTEND_URL"] = "http://frontend.test"
os.environ["GITHUB_CLIENT_ID"] = "test-client-id"
os.environ["GITHUB_CLIENT_SECRET"] = "test-client-secret"
os.environ["GITHUB_REDIRECT_URI"] = "http://testserver/github/callback"

from cryptography.fernet import Fernet

os.environ["GITHUB_TOKEN_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from collections.abc import Iterator  # noqa: E402
from urllib.parse import parse_qs, urlparse  # noqa: E402

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_email_sender,
    get_github_client,
    get_optional_github_client,
)
from app.core import rate_limit
from app.core.database import SessionLocal, engine
from app.main import app
from app.models import Base
from tests.fakes import FakeEmailSender, FakeGitHubClient

REGISTER_PAYLOAD: dict[str, str] = {
    "email": "dev@example.com",
    "password": "password1",
    "full_name": "Dev User",
    "role": "application_developer",
}


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Each test gets its own event loop; drop pooled connections tied to this one.
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(client: AsyncClient) -> AsyncIterator[AsyncSession]:
    """Direct DB access for assertions. Depends on `client` so tables exist,
    and is closed before `client` drops them."""
    async with SessionLocal() as session:
        yield session


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fake_github() -> Iterator[FakeGitHubClient]:
    fake = FakeGitHubClient()
    app.dependency_overrides[get_github_client] = lambda: fake
    app.dependency_overrides[get_optional_github_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_github_client, None)
    app.dependency_overrides.pop(get_optional_github_client, None)


@pytest.fixture(autouse=True)
def outbox() -> Iterator[FakeEmailSender]:
    """Every test gets an empty in-memory outbox instead of real emails."""
    fake = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_email_sender, None)


@pytest.fixture(autouse=True)
def reset_rate_limits() -> Iterator[None]:
    """Limiters are module-level, so counts would leak between tests."""
    for limiter in rate_limit.ALL_LIMITERS:
        limiter.clear()
    yield
    for limiter in rate_limit.ALL_LIMITERS:
        limiter.clear()


async def register_user(
    client: AsyncClient,
    email: str = "dev@example.com",
    **overrides: str,
) -> str:
    """Register a user and return their access token."""
    payload = {**REGISTER_PAYLOAD, "email": email, **overrides}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


async def user_id(client: AsyncClient, token: str) -> str:
    response = await client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 200, response.text
    return response.json()["id"]


def access_token_issued_ago(subject: str, seconds: int) -> str:
    """An access token issued `seconds` ago, i.e. before something that just
    happened (like a password change). Built by hand because `iat` has
    one-second precision and tests run faster than that."""
    from datetime import datetime, timedelta, timezone

    import jwt

    from app.core.config import get_settings
    from app.core.security import ACCESS_TOKEN_TYPE

    settings = get_settings()
    issued = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    return jwt.encode(
        {
            "sub": subject,
            "role": "application_developer",
            "type": ACCESS_TOKEN_TYPE,
            "iat": issued,
            "exp": issued + timedelta(minutes=30),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


async def connect_github(
    client: AsyncClient,
    fake: FakeGitHubClient,
    access_token: str,
    *,
    access: str = "private",
    granted_scopes: set[str] | None = None,
    github_token: str = "gho_test_token",
    code: str = "test-code",
) -> Response:
    """Run the whole OAuth round trip; returns the callback's redirect response."""
    start = await client.get(
        "/github/connect",
        params={"access": access},
        headers=auth_header(access_token),
    )
    assert start.status_code == 200, start.text
    state = parse_qs(urlparse(start.json()["authorization_url"]).query)["state"][0]

    if granted_scopes is None:
        granted_scopes = {"repo"} if access == "private" else {"public_repo"}
    fake.authorize(code, token=github_token, scopes=granted_scopes)
    return await client.get("/github/callback", params={"code": code, "state": state})


def redirect_params(response: Response) -> dict[str, str]:
    """Query params of the frontend URL the callback redirected to."""
    location = response.headers["location"]
    assert location.startswith("http://frontend.test/integrations/github?")
    return {key: values[0] for key, values in parse_qs(urlparse(location).query).items()}

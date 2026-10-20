from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient

from app.core.database import get_session
from app.main import app


class _UnreachableDatabaseSession:
    async def execute(self, *_args: object, **_kwargs: object) -> None:
        raise OSError("connection refused")


async def _unreachable_session() -> AsyncIterator[_UnreachableDatabaseSession]:
    yield _UnreachableDatabaseSession()


@pytest.mark.asyncio
async def test_liveness_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness_returns_ok_when_database_is_up(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.asyncio
async def test_readiness_returns_503_when_database_is_down(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_session] = _unreachable_session
    try:
        response = await client.get("/health/ready")
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 503
    # Generic body only: the underlying error must not leak to callers.
    assert response.json() == {"status": "unavailable", "database": "unavailable"}

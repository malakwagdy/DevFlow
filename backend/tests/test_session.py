import pytest
from httpx import AsyncClient

from app.api.session import initials, slugify
from tests.conftest import auth_header, register_user


@pytest.mark.asyncio
async def test_session_without_company_has_null_workspace(client: AsyncClient) -> None:
    token = await register_user(client, full_name="Alex Vance")
    response = await client.get("/session", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json() == {
        "user": {"name": "Alex Vance", "initials": "AV", "email": "dev@example.com"},
        "workspace": None,
    }


@pytest.mark.asyncio
async def test_session_with_company_returns_workspace(client: AsyncClient) -> None:
    token = await register_user(client, company_name="Acme Production")
    response = await client.get("/session", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["workspace"] == {
        "slug": "acme-production",
        "name": "Acme Production",
        "initials": "AP",
        "cluster": None,
    }


@pytest.mark.asyncio
async def test_session_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/session")
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Alex Vance", "AV"), ("Mary Jane Watson", "MW"), ("Acme", "AC"), ("  ", "")],
)
def test_initials(name: str, expected: str) -> None:
    assert initials(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Acme Production", "acme-production"),
        ("  Café & Co.  ", "cafe-co"),
        ("شركة", ""),
    ],
)
def test_slugify(name: str, expected: str) -> None:
    assert slugify(name) == expected

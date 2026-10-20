import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmailAlreadyRegisteredError
from app.core.security import verify_password
from scripts.create_admin import create_admin


@pytest.mark.asyncio
async def test_create_admin_can_log_in_as_admin(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    admin = await create_admin(db_session, " Admin@Example.com ", "adminpass1", "Root")
    assert admin.email == "admin@example.com"

    response = await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass1"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_create_admin_rejects_duplicate_email(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_admin(db_session, "admin@example.com", "adminpass1", "Root")
    with pytest.raises(EmailAlreadyRegisteredError):
        await create_admin(db_session, "admin@example.com", "adminpass1", "Root")


@pytest.mark.asyncio
async def test_create_admin_rejects_short_password(db_session: AsyncSession) -> None:
    with pytest.raises(ValueError):
        await create_admin(db_session, "admin@example.com", "short", "Root")


def test_verify_password_without_hash_is_false() -> None:
    assert verify_password("anything", None) is False

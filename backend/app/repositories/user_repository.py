import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Persistence operations for user rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        return await self._session.scalar(select(User).where(User.email == email))

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def create(self, user: User) -> User:
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        # Load server-generated columns (created_at, updated_at).
        await self._session.refresh(user)
        return user

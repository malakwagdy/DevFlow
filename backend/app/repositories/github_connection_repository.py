import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_connection import GitHubConnection


class GitHubConnectionRepository:
    """Persistence for users' linked GitHub accounts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> GitHubConnection | None:
        return await self._session.scalar(
            select(GitHubConnection).where(GitHubConnection.user_id == user_id)
        )

    async def save(self, connection: GitHubConnection) -> GitHubConnection:
        self._session.add(connection)
        await self._session.commit()
        # Load server-generated columns (created_at, updated_at).
        await self._session.refresh(connection)
        return connection

    async def delete(self, connection: GitHubConnection) -> None:
        await self._session.delete(connection)
        await self._session.commit()

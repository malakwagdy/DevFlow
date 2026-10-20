import uuid

from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.team import user_teams


def _visible_to(user_id: uuid.UUID) -> ColumnElement[bool]:
    """A user sees projects they own, plus projects of any team they're in."""
    user_team_ids = select(user_teams.c.team_id).where(user_teams.c.user_id == user_id)
    return or_(Project.owner_id == user_id, Project.team_id.in_(user_team_ids))


class ProjectRepository:
    """Persistence operations for project rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_visible(self, user_id: uuid.UUID) -> list[Project]:
        result = await self._session.scalars(
            select(Project)
            .where(_visible_to(user_id))
            .order_by(Project.created_at.desc())
        )
        return list(result)

    async def get_visible(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Project | None:
        return await self._session.scalar(
            select(Project).where(Project.id == project_id, _visible_to(user_id))
        )

    async def get_by_owner_and_repo(
        self,
        owner_id: uuid.UUID,
        github_repo_id: int,
    ) -> Project | None:
        return await self._session.scalar(
            select(Project).where(
                Project.owner_id == owner_id,
                Project.github_repo_id == github_repo_id,
            )
        )

    async def first_team_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        # Prototype: a company user is in exactly one team (the company's Default team).
        return await self._session.scalar(
            select(user_teams.c.team_id).where(user_teams.c.user_id == user_id).limit(1)
        )

    async def save(self, project: Project) -> Project:
        self._session.add(project)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        await self._session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)
        await self._session.commit()

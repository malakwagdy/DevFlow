import uuid

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    PermissionDeniedError,
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
)
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.github_service import GitHubService


class ProjectService:
    """Projects: a GitHub repository registered on DevFlow for deployment."""

    def __init__(self, projects: ProjectRepository) -> None:
        self._projects = projects

    async def create(
        self,
        owner: User,
        payload: ProjectCreate,
        github: GitHubService,
    ) -> Project:
        # Confirms the repo exists and the owner's GitHub access level allows it.
        repo = await github.get_repository(owner, payload.repo_full_name)
        if await self._projects.get_by_owner_and_repo(owner.id, repo.id) is not None:
            raise ProjectAlreadyExistsError()
        branch = payload.branch or repo.default_branch
        await github.ensure_branch_exists(owner, repo, branch)

        description = (
            payload.description
            if "description" in payload.model_fields_set
            else repo.description
        )
        project = Project(
            name=payload.name or repo.name,
            description=description,
            repo_url=repo.html_url,
            github_repo_id=repo.id,
            repo_full_name=repo.full_name,
            default_branch=repo.default_branch,
            branch=branch,
            is_private=repo.private,
            owner_id=owner.id,
            team_id=await self._projects.first_team_id(owner.id),
        )
        try:
            return await self._projects.save(project)
        except IntegrityError as exc:
            raise ProjectAlreadyExistsError() from exc

    async def list_for(self, user: User) -> list[Project]:
        return await self._projects.list_visible(user.id)

    async def get(self, user: User, project_id: uuid.UUID) -> Project:
        project = await self._projects.get_visible(project_id, user.id)
        if project is None:
            raise ProjectNotFoundError()
        return project

    async def update(
        self,
        user: User,
        project_id: uuid.UUID,
        payload: ProjectUpdate,
        github: GitHubService,
    ) -> Project:
        project = await self._get_owned(user, project_id)
        # ProjectUpdate rejects `branch: null`, so None here means "not sent".
        if payload.branch is not None and payload.branch != project.branch:
            # Re-fetch the repo: access may have changed since the project was created.
            repo = await github.get_repository(user, project.repo_full_name)
            await github.ensure_branch_exists(user, repo, payload.branch)
        for field in payload.model_fields_set:
            setattr(project, field, getattr(payload, field))
        return await self._projects.save(project)

    async def delete(self, user: User, project_id: uuid.UUID) -> None:
        project = await self._get_owned(user, project_id)
        await self._projects.delete(project)

    async def _get_owned(self, user: User, project_id: uuid.UUID) -> Project:
        # Teammates can view a project; only its owner can change or delete it.
        project = await self.get(user, project_id)
        if project.owner_id != user.id:
            raise PermissionDeniedError()
        return project

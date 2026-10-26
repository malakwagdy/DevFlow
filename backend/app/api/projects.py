import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import CurrentUserDep, GitHubServiceDep, SessionDep
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(session: SessionDep) -> ProjectService:
    return ProjectService(ProjectRepository(session))


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    current_user: CurrentUserDep,
    projects: ProjectServiceDep,
    github: GitHubServiceDep,
) -> Project:
    """Create a project from one of the user's GitHub repositories."""
    return await projects.create(current_user, payload, github)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: CurrentUserDep,
    projects: ProjectServiceDep,
) -> list[Project]:
    """Projects you own, plus your team's projects."""
    return await projects.list_for(current_user)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    projects: ProjectServiceDep,
) -> Project:
    return await projects.get(current_user, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: CurrentUserDep,
    projects: ProjectServiceDep,
    github: GitHubServiceDep,
) -> Project:
    """Changing `branch` checks on GitHub that it exists."""
    return await projects.update(current_user, project_id, payload, github)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    projects: ProjectServiceDep,
) -> Response:
    await projects.delete(current_user, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

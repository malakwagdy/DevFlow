from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    AccountEmailServiceDep,
    CurrentUserDep,
    OptionalGitHubServiceDep,
    SessionDep,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import (
    AccountDeleteRequest,
    PasswordChangeRequest,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(session: SessionDep, emails: AccountEmailServiceDep) -> UserService:
    return UserService(UserRepository(session), emails)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: CurrentUserDep,
    users: UserServiceDep,
) -> User:
    """Change `full_name` and/or `email`. A new email needs `current_password`,
    becomes unverified, and gets a verification link; the old one is notified."""
    return await users.update_profile(current_user, payload)


@router.post("/me/password", response_model=TokenResponse)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: CurrentUserDep,
    users: UserServiceDep,
) -> TokenResponse:
    """Signs out every session, this one included; use the returned token."""
    return await users.change_password(current_user, payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    payload: AccountDeleteRequest,
    current_user: CurrentUserDep,
    users: UserServiceDep,
    github: OptionalGitHubServiceDep,
) -> Response:
    """Permanently deletes the account and its projects, and revokes GitHub
    access. A sole company owner's company is deleted too. Needs `password`."""
    await users.delete_account(current_user, payload, github)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

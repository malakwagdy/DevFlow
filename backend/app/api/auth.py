from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUserDep, SessionDep
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(UserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    return await auth_service.register(payload)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    return await auth_service.login(payload)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
async def me(current_user: CurrentUserDep) -> User:
    return current_user

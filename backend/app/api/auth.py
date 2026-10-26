from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies import AccountEmailServiceDep, CurrentUserDep, SessionDep
from app.core import rate_limit
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for this email, we've sent a link to reset the password."
)
TOO_MANY_ATTEMPTS = {status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limited"}}


def get_auth_service(session: SessionDep, emails: AccountEmailServiceDep) -> AuthService:
    return AuthService(UserRepository(session), emails)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
    responses=TOO_MANY_ATTEMPTS,
)
async def register(
    payload: RegisterRequest,
    request: Request,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """Also emails a verification link."""
    rate_limit.register_by_ip.hit(rate_limit.client_ip(request))
    return await auth_service.register(payload)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    responses=TOO_MANY_ATTEMPTS,
)
async def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """Limited per IP, and per email after repeated wrong passwords."""
    rate_limit.login_by_ip.hit(rate_limit.client_ip(request))
    return await auth_service.login(payload)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
async def me(current_user: CurrentUserDep) -> User:
    return current_user


# --- email verification -----------------------------------------------------------


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    responses=TOO_MANY_ATTEMPTS,
)
async def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    auth_service: AuthServiceDep,
) -> User:
    """`token` comes from the emailed link. No login needed: the link may be
    opened on another device."""
    rate_limit.link_tokens_by_ip.hit(rate_limit.client_ip(request))
    return await auth_service.verify_email(payload.token)


@router.post(
    "/resend-verification",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=TOO_MANY_ATTEMPTS,
)
async def resend_verification(
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> Response:
    await auth_service.resend_verification(current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- password reset -------------------------------------------------------------


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MessageResponse,
    responses=TOO_MANY_ATTEMPTS,
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    auth_service: AuthServiceDep,
) -> MessageResponse:
    """Same answer whether or not the account exists."""
    rate_limit.forgot_password_by_ip.hit(rate_limit.client_ip(request))
    await auth_service.forgot_password(str(payload.email))
    return MessageResponse(detail=FORGOT_PASSWORD_MESSAGE)


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=TOO_MANY_ATTEMPTS,
)
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    auth_service: AuthServiceDep,
) -> Response:
    """`token` comes from the emailed link. Signs out every session; the user
    then signs in with the new password."""
    rate_limit.link_tokens_by_ip.hit(rate_limit.client_ip(request))
    await auth_service.reset_password(payload.token, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

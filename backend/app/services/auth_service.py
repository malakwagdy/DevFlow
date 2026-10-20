from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.company import Company
from app.models.team import Team
from app.models.user import CompanyRole, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse

# Prototype: a new company gets exactly one team, holding only its owner.
DEFAULT_TEAM_NAME = "Default"


class AuthService:
    """Registration and login business logic."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        email = str(payload.email).lower()
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError()

        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role,
        )
        if payload.company_name is not None:
            company = Company(name=payload.company_name)
            user.company = company
            user.company_role = CompanyRole.owner
            user.teams.append(Team(name=DEFAULT_TEAM_NAME, company=company))

        # The company, team and membership rows are saved with the user in one
        # transaction, so a failed signup leaves nothing behind.
        try:
            created = await self._users.create(user)
        except IntegrityError as exc:
            raise EmailAlreadyRegisteredError() from exc

        return self._issue_token(created)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        email = str(payload.email).lower()
        user = await self._users.get_by_email(email)
        # Always run the password hash, even for unknown emails (timing-safe).
        password_ok = verify_password(
            payload.password,
            user.hashed_password if user is not None else None,
        )
        if user is None or not password_ok:
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError()
        return self._issue_token(user)

    def _issue_token(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role.value),
            user=UserResponse.model_validate(user),
        )

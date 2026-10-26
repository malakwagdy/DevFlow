import hmac
import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core import rate_limit
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    EmailAlreadyVerifiedError,
    EmailVerificationTokenInvalidError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordResetTokenInvalidError,
)
from app.core.security import (
    create_access_token,
    decode_email_verification_token,
    decode_password_reset_token,
    hash_password,
    password_fingerprint,
    verify_password,
)
from app.models.company import Company
from app.models.team import Team
from app.models.user import CompanyRole, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.account_email_service import AccountEmailService

# Prototype: a new company gets exactly one team, holding only its owner.
DEFAULT_TEAM_NAME = "Default"


def issue_token(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        user=UserResponse.model_validate(user),
    )


class AuthService:
    """Registration, login, email verification and password reset."""

    def __init__(self, users: UserRepository, emails: AccountEmailService) -> None:
        self._users = users
        self._emails = emails

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

        self._emails.send_verification(created)
        return issue_token(created)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        email = str(payload.email).lower()
        # Checked before the password, so a locked-out account stays locked
        # even when the right password is finally guessed.
        rate_limit.login_failures_by_email.check(email)

        user = await self._users.get_by_email(email)
        # Always run the password hash, even for unknown emails (timing-safe).
        password_ok = verify_password(
            payload.password,
            user.hashed_password if user is not None else None,
        )
        if user is None or not password_ok:
            # Unknown emails count too, so the limit doesn't reveal which exist.
            rate_limit.login_failures_by_email.hit(email)
            raise InvalidCredentialsError()
        rate_limit.login_failures_by_email.reset(email)
        if not user.is_active:
            raise InactiveUserError()
        return issue_token(user)

    # --- email verification -------------------------------------------------------

    async def verify_email(self, token: str) -> User:
        try:
            payload = decode_email_verification_token(token)
            user_id = uuid.UUID(payload["sub"])
        except (InvalidTokenError, KeyError, ValueError):
            raise EmailVerificationTokenInvalidError() from None

        user = await self._users.get_by_id(user_id)
        # The link is for the address it was sent to; an email change voids it.
        if user is None or user.email != payload.get("email"):
            raise EmailVerificationTokenInvalidError()
        if user.email_verified_at is None:  # clicking the link twice is fine
            user.email_verified_at = datetime.now(timezone.utc)
            user = await self._users.save(user)
        return user

    async def resend_verification(self, user: User) -> None:
        if user.email_verified_at is not None:
            raise EmailAlreadyVerifiedError()
        rate_limit.resend_verification_by_user.hit(str(user.id))
        self._emails.send_verification(user)

    # --- password reset -----------------------------------------------------------

    async def forgot_password(self, email: str) -> None:
        """Emails a reset link if the account exists. Callers must respond the
        same way either way, so this can't be used to discover accounts."""
        email = email.lower()
        rate_limit.forgot_password_by_email.hit(email)
        user = await self._users.get_by_email(email)
        if user is not None and user.is_active:
            self._emails.send_password_reset(user)

    async def reset_password(self, token: str, new_password: str) -> None:
        try:
            payload = decode_password_reset_token(token)
            user_id = uuid.UUID(payload["sub"])
            fingerprint = str(payload["pwd"])
        except (InvalidTokenError, KeyError, ValueError):
            raise PasswordResetTokenInvalidError() from None

        user = await self._users.get_by_id(user_id)
        if (
            user is None
            or not user.is_active
            or user.email != payload.get("email")
            # Fails once the password has changed, which makes the link single-use.
            or not hmac.compare_digest(fingerprint, password_fingerprint(user.hashed_password))
        ):
            raise PasswordResetTokenInvalidError()

        now = datetime.now(timezone.utc)
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = now  # signs out every existing session
        # Opening the emailed link proved the user reads this inbox.
        user.email_verified_at = user.email_verified_at or now
        await self._users.save(user)
        # The owner just proved who they are, so lift any login lockout.
        rate_limit.login_failures_by_email.reset(user.email)
        self._emails.send_password_changed(user)

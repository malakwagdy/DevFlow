from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core import rate_limit
from app.core.exceptions import (
    CompanyHasOtherMembersError,
    EmailAlreadyRegisteredError,
    IncorrectPasswordError,
)
from app.core.security import hash_password, verify_password
from app.models.user import CompanyRole, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import AccountDeleteRequest, PasswordChangeRequest, UserUpdate
from app.services.account_email_service import AccountEmailService
from app.services.auth_service import issue_token
from app.services.github_service import GitHubService


class UserService:
    """The signed-in user managing their own account (the Settings page)."""

    def __init__(self, users: UserRepository, emails: AccountEmailService) -> None:
        self._users = users
        self._emails = emails

    async def update_profile(self, user: User, payload: UserUpdate) -> User:
        old_email = user.email
        new_email = str(payload.email).lower() if payload.email is not None else None
        email_changes = new_email is not None and new_email != old_email

        if email_changes:
            assert payload.current_password is not None  # enforced by UserUpdate
            self._confirm_password(user, payload.current_password)
            if await self._users.get_by_email(new_email) is not None:
                raise EmailAlreadyRegisteredError()
            user.email = new_email
            user.email_verified_at = None  # the new address isn't proven yet
        if payload.full_name is not None:
            user.full_name = payload.full_name

        try:
            user = await self._users.save(user)
        except IntegrityError as exc:  # someone took the address meanwhile
            raise EmailAlreadyRegisteredError() from exc

        if email_changes:
            self._emails.send_verification(user)
            self._emails.send_email_changed(user, old_email)
        return user

    async def change_password(self, user: User, payload: PasswordChangeRequest) -> TokenResponse:
        """Signs out every session, including this one, so a fresh token is returned."""
        self._confirm_password(user, payload.current_password)
        user.hashed_password = hash_password(payload.new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user = await self._users.save(user)
        self._emails.send_password_changed(user)
        return issue_token(user)

    async def delete_account(
        self,
        user: User,
        payload: AccountDeleteRequest,
        github: GitHubService | None,
    ) -> None:
        """Deletes the user, their projects and, for a sole owner, their company."""
        self._confirm_password(user, payload.password)

        delete_company = False
        if user.company_id is not None and user.company_role is CompanyRole.owner:
            if await self._users.count_company_members(user.company_id) > 1:
                raise CompanyHasOtherMembersError()
            delete_company = True

        if github is not None:
            await github.disconnect_if_connected(user)
        await self._users.delete_account(user, delete_company=delete_company)

    def _confirm_password(self, user: User, password: str) -> None:
        key = str(user.id)
        rate_limit.password_confirm_failures_by_user.check(key)
        if not verify_password(password, user.hashed_password):
            rate_limit.password_confirm_failures_by_user.hit(key)
            raise IncorrectPasswordError()
        rate_limit.password_confirm_failures_by_user.reset(key)

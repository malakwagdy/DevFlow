from urllib.parse import urlencode

from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.core.security import create_email_verification_token, create_password_reset_token
from app.integrations.email import EmailMessage, EmailSender
from app.models.user import User

# Frontend pages the links open; they POST the token back to the API.
VERIFY_EMAIL_PATH = "/verify-email"
RESET_PASSWORD_PATH = "/reset-password"


class AccountEmailService:
    """Builds account emails and sends them after the response has gone out,
    so the API never waits on the mail server and response times don't reveal
    whether an email was actually sent."""

    def __init__(self, sender: EmailSender, background_tasks: BackgroundTasks) -> None:
        self._sender = sender
        self._background_tasks = background_tasks

    def send_verification(self, user: User) -> None:
        settings = get_settings()
        token = create_email_verification_token(str(user.id), user.email)
        link = self._link(VERIFY_EMAIL_PATH, token)
        self._send(
            EmailMessage(
                to=user.email,
                subject="Verify your DevFlow email address",
                body=(
                    f"Hi {user.full_name},\n\n"
                    f"Confirm this is your email address by opening the link below:\n\n"
                    f"{link}\n\n"
                    f"The link expires in {settings.email_verification_expire_hours} hours. "
                    f"If you didn't create a DevFlow account, you can ignore this email.\n"
                ),
            )
        )

    def send_password_reset(self, user: User) -> None:
        settings = get_settings()
        token = create_password_reset_token(str(user.id), user.email, user.hashed_password)
        link = self._link(RESET_PASSWORD_PATH, token)
        self._send(
            EmailMessage(
                to=user.email,
                subject="Reset your DevFlow password",
                body=(
                    f"Hi {user.full_name},\n\n"
                    f"Someone asked to reset the password for your DevFlow account. "
                    f"To choose a new password, open the link below:\n\n"
                    f"{link}\n\n"
                    f"The link expires in {settings.password_reset_expire_minutes} minutes "
                    f"and works once. If you didn't ask for this, ignore this email; "
                    f"your password stays the same.\n"
                ),
            )
        )

    def send_password_changed(self, user: User) -> None:
        self._send(
            EmailMessage(
                to=user.email,
                subject="Your DevFlow password was changed",
                body=(
                    f"Hi {user.full_name},\n\n"
                    f"The password for your DevFlow account was just changed, and every "
                    f"device was signed out. If this wasn't you, reset your password "
                    f"right away using \"Forgot password?\" on the sign-in page.\n"
                ),
            )
        )

    def send_email_changed(self, user: User, old_email: str) -> None:
        """Warns the previous address, in case the account was taken over."""
        self._send(
            EmailMessage(
                to=old_email,
                subject="Your DevFlow email address was changed",
                body=(
                    f"Hi {user.full_name},\n\n"
                    f"The email address of your DevFlow account was changed from "
                    f"{old_email} to {user.email}. If this wasn't you, contact support.\n"
                ),
            )
        )

    def _send(self, message: EmailMessage) -> None:
        self._background_tasks.add_task(self._sender.send, message)

    @staticmethod
    def _link(path: str, token: str) -> str:
        base = get_settings().frontend_url.rstrip("/")
        return f"{base}{path}?{urlencode({'token': token})}"

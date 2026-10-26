"""Sending emails. Pick the backend with EMAIL_BACKEND (see config.py).

Senders never raise: a failed email is logged, because it is sent after the
HTTP response has already gone out.
"""

import asyncio
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage

from app.core.config import Settings

logger = logging.getLogger(__name__)

_SMTP_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str  # plain text


class EmailSender:
    async def send(self, message: EmailMessage) -> None:
        raise NotImplementedError


class ConsoleEmailSender(EmailSender):
    """Development: prints the email to the server log so links can be copied."""

    async def send(self, message: EmailMessage) -> None:
        logger.warning(
            "Email (console backend, not sent)\nTo: %s\nSubject: %s\n\n%s",
            message.to,
            message.subject,
            message.body,
        )


class SmtpEmailSender(EmailSender):
    def __init__(self, settings: Settings) -> None:
        if settings.smtp_host is None:
            raise ValueError("EMAIL_BACKEND=smtp needs SMTP_HOST")
        self._settings = settings

    async def send(self, message: EmailMessage) -> None:
        # smtplib blocks, so run it off the event loop.
        try:
            await asyncio.to_thread(self._send_blocking, message)
        except (OSError, smtplib.SMTPException):
            logger.exception("Could not send email %r to %s", message.subject, message.to)

    def _send_blocking(self, message: EmailMessage) -> None:
        settings = self._settings
        mime = MimeMessage()
        mime["From"] = settings.email_from
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.body)

        assert settings.smtp_host is not None
        with smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=_SMTP_TIMEOUT_SECONDS
        ) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(mime)

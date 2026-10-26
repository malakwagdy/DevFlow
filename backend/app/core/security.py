import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.core.exceptions import GitHubNotConfiguredError, InvalidTokenError

_password_hasher = PasswordHasher()

# Verified against when the email is unknown, so a login for a missing user
# takes as long as one with a wrong password (no email enumeration by timing).
_DUMMY_HASH = _password_hasher.hash("devflow-timing-equalizer")

# Every JWT we sign carries a "type", so one kind can never be used as another
# (e.g. an OAuth state value can't be replayed as a login token).
ACCESS_TOKEN_TYPE = "access"
OAUTH_STATE_TOKEN_TYPE = "github_oauth_state"
OAUTH_STATE_EXPIRE_MINUTES = 10
EMAIL_VERIFICATION_TOKEN_TYPE = "email_verification"
PASSWORD_RESET_TOKEN_TYPE = "password_reset"


class SecretDecryptionError(Exception):
    """Stored ciphertext can't be decrypted (corrupted, or the key changed)."""


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    """Check a password; pass `None` for an unknown user to spend the same time."""
    try:
        _password_hasher.verify(hashed_password or _DUMMY_HASH, password)
    except VerifyMismatchError:
        return False
    return hashed_password is not None


def create_access_token(subject: str, role: str) -> str:
    lifetime = timedelta(minutes=get_settings().access_token_expire_minutes)
    return _encode({"sub": subject, "role": role, "type": ACCESS_TOKEN_TYPE}, lifetime)


def decode_access_token(token: str) -> dict[str, Any]:
    return _decode(token, ACCESS_TOKEN_TYPE)


def create_oauth_state(user_id: str, access: str) -> str:
    """Signed, short-lived `state` for the GitHub OAuth round trip.

    It identifies which DevFlow user started the flow (the callback arrives
    without our Authorization header) and stops forged callbacks.
    """
    claims = {
        "sub": user_id,
        "access": access,
        "type": OAUTH_STATE_TOKEN_TYPE,
        "nonce": secrets.token_urlsafe(16),
    }
    return _encode(claims, timedelta(minutes=OAUTH_STATE_EXPIRE_MINUTES))


def decode_oauth_state(state: str) -> dict[str, Any]:
    return _decode(state, OAUTH_STATE_TOKEN_TYPE)


def create_email_verification_token(user_id: str, email: str) -> str:
    """Link token proving the user can read `email`. It carries the address, so
    a link sent before an email change can't verify the new address."""
    lifetime = timedelta(hours=get_settings().email_verification_expire_hours)
    claims = {"sub": user_id, "email": email, "type": EMAIL_VERIFICATION_TOKEN_TYPE}
    return _encode(claims, lifetime)


def decode_email_verification_token(token: str) -> dict[str, Any]:
    return _decode(token, EMAIL_VERIFICATION_TOKEN_TYPE)


def create_password_reset_token(user_id: str, email: str, hashed_password: str) -> str:
    """Single-use without a database table: it embeds a fingerprint of the
    current password hash, so it stops working once the password changes."""
    lifetime = timedelta(minutes=get_settings().password_reset_expire_minutes)
    claims = {
        "sub": user_id,
        "email": email,
        "pwd": password_fingerprint(hashed_password),
        "type": PASSWORD_RESET_TOKEN_TYPE,
    }
    return _encode(claims, lifetime)


def decode_password_reset_token(token: str) -> dict[str, Any]:
    return _decode(token, PASSWORD_RESET_TOKEN_TYPE)


def password_fingerprint(hashed_password: str) -> str:
    # Keyed, so the (readable) token reveals nothing usable about the hash.
    key = get_settings().jwt_secret.encode()
    return hmac.new(key, hashed_password.encode(), hashlib.sha256).hexdigest()[:32]


def issued_before(payload: dict[str, Any], moment: datetime | None) -> bool:
    """True if the token was issued before `moment` (e.g. a password change).

    `iat` has whole-second precision, so compare against the start of that second:
    a token issued right after the change, in the same second, stays valid.
    """
    if moment is None:
        return False
    return int(payload["iat"]) < int(moment.timestamp())


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise SecretDecryptionError() from exc


def _fernet() -> Fernet:
    key = get_settings().github_token_encryption_key
    if key is None:
        raise GitHubNotConfiguredError()
    return Fernet(key.encode())


def _encode(claims: dict[str, Any], lifetime: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {**claims, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode(token: str, expected_type: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc
    if payload["type"] != expected_type:
        raise InvalidTokenError()
    return payload

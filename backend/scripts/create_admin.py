"""Create a platform admin (public registration cannot).

Usage, from the backend/ folder:
    python -m scripts.create_admin --email admin@example.com --name "Admin"
The password is prompted for, so it never ends up in shell history.
"""

import argparse
import asyncio
import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal, engine
from app.core.exceptions import EmailAlreadyRegisteredError
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

MIN_PASSWORD_LENGTH = 8


async def create_admin(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str,
) -> User:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    users = UserRepository(session)
    email = email.strip().lower()
    if await users.get_by_email(email) is not None:
        raise EmailAlreadyRegisteredError()

    return await users.create(
        User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name.strip(),
            role=UserRole.admin,
        )
    )


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Create a DevFlow admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="Full name")
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords do not match")

    try:
        async with SessionLocal() as session:
            admin = await create_admin(session, args.email, password, args.name)
    except (ValueError, EmailAlreadyRegisteredError) as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        await engine.dispose()
    print(f"Created admin {admin.email} ({admin.id})")


if __name__ == "__main__":
    asyncio.run(_main())

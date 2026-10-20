import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, ForeignKey, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class GitHubAccess(str, Enum):
    """What the user agreed to let DevFlow see. Chosen per user at connect time."""

    public = "public"  # GitHub scope `public_repo`
    private = "private"  # GitHub scope `repo` (public + private)


class GitHubConnection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "github_connections"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    github_user_id: Mapped[int] = mapped_column(BigInteger)
    github_login: Mapped[str] = mapped_column(String(255))
    # Fernet-encrypted OAuth token; never returned by the API or logged.
    encrypted_access_token: Mapped[str] = mapped_column(Text)
    # Scopes GitHub actually granted, comma-separated (e.g. "repo").
    scopes: Mapped[str] = mapped_column(String(255))
    access: Mapped[GitHubAccess] = mapped_column(SAEnum(GitHubAccess, name="github_access"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

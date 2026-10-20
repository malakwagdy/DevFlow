import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


class Project(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("owner_id", "github_repo_id"),)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    repo_url: Mapped[str | None] = mapped_column(String(2048))
    # GitHub's numeric id survives repo renames/transfers; full_name is for display/API calls.
    github_repo_id: Mapped[int] = mapped_column(BigInteger)
    repo_full_name: Mapped[str] = mapped_column(String(255))
    default_branch: Mapped[str] = mapped_column(String(255))
    is_private: Mapped[bool]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    team: Mapped["Team | None"] = relationship(back_populates="projects")

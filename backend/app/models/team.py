import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.project import Project
    from app.models.user import User

user_teams = Table(
    "user_teams",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "team_id",
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Team(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("company_id", "name"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(255))

    company: Mapped["Company"] = relationship(back_populates="teams")
    members: Mapped[list["User"]] = relationship(
        secondary=user_teams,
        back_populates="teams",
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="team")

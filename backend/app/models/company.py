from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


class Company(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(back_populates="company")
    teams: Mapped[list["Team"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.team import user_teams

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.project import Project
    from app.models.team import Team


class UserRole(str, Enum):
    # until further development, we will only have these roles le7ad mashoof actually met7ageen eh : ~yehia
    application_developer = "application_developer"
    devops_engineer = "devops_engineer"
    admin = "admin"


class CompanyRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class User(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"))
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        index=True,
    )
    company_role: Mapped[CompanyRole | None] = mapped_column(
        SAEnum(CompanyRole, name="company_role"),
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    company: Mapped["Company | None"] = relationship(back_populates="users")
    teams: Mapped[list["Team"]] = relationship(
        secondary=user_teams,
        back_populates="members",
    )
    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")

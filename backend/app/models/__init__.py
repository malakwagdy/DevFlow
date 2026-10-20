# Import every model so Base.metadata is complete (used by Alembic and tests).
from app.models.base import Base
from app.models.company import Company
from app.models.github_connection import GitHubAccess, GitHubConnection
from app.models.project import Project
from app.models.team import Team, user_teams
from app.models.user import CompanyRole, User, UserRole

__all__ = [
    "Base",
    "Company",
    "CompanyRole",
    "GitHubAccess",
    "GitHubConnection",
    "Project",
    "Team",
    "User",
    "UserRole",
    "user_teams",
]

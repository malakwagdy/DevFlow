"""initial schema: companies, users, teams, user_teams, projects

Revision ID: 0001
Revises:
Create Date: 2026-10-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID_DEFAULT = sa.text("gen_random_uuid()")

user_role = sa.Enum(
    "application_developer", "devops_engineer", "admin", name="user_role"
)
company_role = sa.Enum("owner", "admin", "member", name="company_role")


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("company_role", company_role, nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_users_company_id_companies"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_company_id"), "users", ["company_id"])

    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_teams_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teams")),
        sa.UniqueConstraint(
            "company_id", "name", name=op.f("uq_teams_company_id_name")
        ),
    )

    op.create_table(
        "user_teams",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_teams_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("fk_user_teams_team_id_teams"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "team_id", name=op.f("pk_user_teams")),
    )
    op.create_index(op.f("ix_user_teams_team_id"), "user_teams", ["team_id"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("repo_url", sa.String(2048), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_projects_owner_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("fk_projects_team_id_teams"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_projects_owner_id"), "projects", ["owner_id"])
    op.create_index(op.f("ix_projects_team_id"), "projects", ["team_id"])


def downgrade() -> None:
    op.drop_table("projects")
    op.drop_table("user_teams")
    op.drop_table("teams")
    op.drop_table("users")
    op.drop_table("companies")
    company_role.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)

"""github_connections table; link projects to GitHub repositories

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

github_access = sa.Enum("public", "private", name="github_access")


def upgrade() -> None:
    op.create_table(
        "github_connections",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("github_user_id", sa.BigInteger(), nullable=False),
        sa.Column("github_login", sa.String(255), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("scopes", sa.String(255), nullable=False),
        sa.Column("access", github_access, nullable=False),
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
            ["user_id"],
            ["users.id"],
            name=op.f("fk_github_connections_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_github_connections")),
        sa.UniqueConstraint("user_id", name=op.f("uq_github_connections_user_id")),
    )

    # NOT NULL without defaults: fine while `projects` is empty (nothing could
    # create projects before this revision).
    op.add_column("projects", sa.Column("github_repo_id", sa.BigInteger(), nullable=False))
    op.add_column("projects", sa.Column("repo_full_name", sa.String(255), nullable=False))
    op.add_column("projects", sa.Column("default_branch", sa.String(255), nullable=False))
    op.add_column("projects", sa.Column("is_private", sa.Boolean(), nullable=False))
    op.create_unique_constraint(
        op.f("uq_projects_owner_id_github_repo_id"),
        "projects",
        ["owner_id", "github_repo_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_projects_owner_id_github_repo_id"), "projects", type_="unique"
    )
    op.drop_column("projects", "is_private")
    op.drop_column("projects", "default_branch")
    op.drop_column("projects", "repo_full_name")
    op.drop_column("projects", "github_repo_id")
    op.drop_table("github_connections")
    github_access.drop(op.get_bind(), checkfirst=True)

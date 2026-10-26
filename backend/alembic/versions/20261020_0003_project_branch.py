"""projects.branch: the branch chosen for builds and deploys

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-20

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Existing projects track their repo's default branch, as they did implicitly.
    op.add_column("projects", sa.Column("branch", sa.String(255), nullable=True))
    op.execute("UPDATE projects SET branch = default_branch")
    op.alter_column("projects", "branch", nullable=False)


def downgrade() -> None:
    op.drop_column("projects", "branch")

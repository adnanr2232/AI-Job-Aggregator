"""candidate profiles + run profile + limits

Revision ID: 892c91aaffe3
Revises: ed045dda9c96
Create Date: 2026-02-27 10:43:16.077186

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "892c91aaffe3"
down_revision: str | Sequence[str] | None = "ed045dda9c96"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column("name", sa.String(length=256), nullable=True),
        sa.Column("location", sa.String(length=256), nullable=True),
        sa.Column("role", sa.String(length=256), nullable=True),
        sa.Column("skills", sqlite.JSON(), nullable=False),
        sa.Column("data", sqlite.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_candidate_profiles_label"), "candidate_profiles", ["label"], unique=True
    )

    # SQLite can't ALTER to add FK constraints; use batch mode for copy-and-move.
    with op.batch_alter_table("ingestion_runs") as batch_op:
        batch_op.add_column(sa.Column("profile_id", sa.Integer(), nullable=True))
        batch_op.create_index(op.f("ix_ingestion_runs_profile_id"), ["profile_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_ingestion_runs_profile_id_candidate_profiles",
            "candidate_profiles",
            ["profile_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("ingestion_runs") as batch_op:
        batch_op.drop_constraint(
            "fk_ingestion_runs_profile_id_candidate_profiles",
            type_="foreignkey",
        )
        batch_op.drop_index(op.f("ix_ingestion_runs_profile_id"))
        batch_op.drop_column("profile_id")

    op.drop_index(op.f("ix_candidate_profiles_label"), table_name="candidate_profiles")
    op.drop_table("candidate_profiles")

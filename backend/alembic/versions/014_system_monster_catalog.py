"""System monster catalog for D&D 5e SRD spawn.

Revision ID: 014
Revises: 013
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_monster_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("system_id", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_normalized", sa.String(length=255), nullable=False),
        sa.Column("challenge_rating", sa.Float(), nullable=False),
        sa.Column("creature_type", sa.String(length=64), nullable=False),
        sa.Column("size", sa.String(length=32), nullable=False),
        sa.Column("source_document", sa.String(length=128), nullable=False),
        sa.Column(
            "narrative_template",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "sheet_template",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("raw_stat_block", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_id", "slug", name="uq_system_monster_catalog_system_slug"),
    )
    op.create_index("idx_system_monster_catalog_system", "system_monster_catalog", ["system_id"])
    op.create_index(
        "idx_system_monster_catalog_name_normalized",
        "system_monster_catalog",
        ["system_id", "name_normalized"],
    )


def downgrade() -> None:
    op.drop_index("idx_system_monster_catalog_name_normalized", table_name="system_monster_catalog")
    op.drop_index("idx_system_monster_catalog_system", table_name="system_monster_catalog")
    op.drop_table("system_monster_catalog")

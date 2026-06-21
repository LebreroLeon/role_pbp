"""Add source_label to system_monster_catalog.

Revision ID: 016
Revises: 015
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "system_monster_catalog",
        sa.Column("source_label", sa.String(length=255), nullable=False, server_default=""),
    )
    op.execute(
        """
        UPDATE system_monster_catalog
        SET source_label = 'SRD 5.1'
        WHERE source_document = 'srd-2014' AND source_label = ''
        """
    )


def downgrade() -> None:
    op.drop_column("system_monster_catalog", "source_label")

"""Add scene_number and display_name to scenes.

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scenes", sa.Column("scene_number", sa.Integer(), nullable=True))
    op.add_column("scenes", sa.Column("display_name", sa.String(length=200), nullable=True))

    op.execute(
        """
        WITH numbered AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY created_at) AS num
            FROM scenes
        )
        UPDATE scenes
        SET scene_number = numbered.num
        FROM numbered
        WHERE scenes.id = numbered.id
        """
    )

    op.alter_column("scenes", "scene_number", nullable=False)
    op.create_index("ix_scenes_campaign_id_scene_number", "scenes", ["campaign_id", "scene_number"])


def downgrade() -> None:
    op.drop_index("ix_scenes_campaign_id_scene_number", table_name="scenes")
    op.drop_column("scenes", "display_name")
    op.drop_column("scenes", "scene_number")

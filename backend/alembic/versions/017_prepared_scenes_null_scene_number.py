"""Prepared scenes keep scene_number NULL until activation.

Revision ID: 017
Revises: 016
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("scenes", "scene_number", existing_type=sa.Integer(), nullable=True)
    op.execute("UPDATE scenes SET scene_number = NULL WHERE status = 'PREPARED'")


def downgrade() -> None:
    op.execute(
        """
        UPDATE scenes
        SET scene_number = sub.num
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY campaign_id
                       ORDER BY COALESCE(scene_number, 999999), created_at
                   ) AS num
            FROM scenes
            WHERE scene_number IS NULL
        ) AS sub
        WHERE scenes.id = sub.id
        """
    )
    op.alter_column("scenes", "scene_number", existing_type=sa.Integer(), nullable=False)

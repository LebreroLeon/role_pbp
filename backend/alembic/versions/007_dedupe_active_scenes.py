"""Keep only the most recent ACTIVE scene per campaign; pause the rest.

Revision ID: 007
Revises: 006
"""

from typing import Sequence, Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                scene_state ? 'metadata' AS has_metadata,
                ROW_NUMBER() OVER (
                    PARTITION BY campaign_id
                    ORDER BY updated_at DESC, created_at DESC
                ) AS rn
            FROM scenes
            WHERE status = 'ACTIVE'
        )
        UPDATE scenes
        SET
            status = 'PAUSED',
            scene_state = CASE
                WHEN ranked.has_metadata THEN
                    jsonb_set(scenes.scene_state, '{metadata,status}', '"PAUSED"')
                ELSE
                    jsonb_set(scenes.scene_state, '{status}', '"PAUSED"')
            END
        FROM ranked
        WHERE scenes.id = ranked.id
          AND ranked.rn > 1
        """
    )


def downgrade() -> None:
    # Data migration: cannot restore which scenes were duplicate ACTIVE.
    pass

"""Backfill campaigns.game_system for rows created before system selection existed.

Revision ID: 005
Revises: 004
"""

from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE campaigns
        SET game_system = 'dnd5e'
        WHERE game_system IS NULL
           OR TRIM(game_system) = ''
           OR game_system NOT IN ('dnd5e', 'cyberpunk_red', 'vtm_v5')
        """
    )


def downgrade() -> None:
    # Data migration: cannot restore previous NULL/invalid values.
    pass

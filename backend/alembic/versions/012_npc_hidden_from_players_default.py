"""Backfill hidden_from_players on NPC state_flags.

Revision ID: 012
Revises: 011
"""

from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE campaign_entities
        SET document = jsonb_set(
            document,
            '{state_flags,hidden_from_players}',
            'false'::jsonb,
            true
        )
        WHERE entity_type = 'NPC'
          AND (document->'state_flags'->>'hidden_from_players') IS NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE campaign_entities
        SET document = document #- '{state_flags,hidden_from_players}'
        WHERE entity_type = 'NPC'
          AND document->'state_flags' ? 'hidden_from_players'
        """
    )

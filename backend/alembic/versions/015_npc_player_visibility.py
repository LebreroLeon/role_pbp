"""Backfill player_visibility on NPC state_flags.

Revision ID: 015
Revises: 014
"""

from typing import Sequence, Union

from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE campaign_entities
        SET document = jsonb_set(
            document,
            '{state_flags,player_visibility}',
            '"visible"'::jsonb,
            true
        )
        WHERE entity_type = 'NPC'
          AND (document->'state_flags'->>'player_visibility') IS NULL
        """
    )
    op.execute(
        """
        UPDATE campaign_entities
        SET document = jsonb_set(
            jsonb_set(
                document,
                '{state_flags,player_visibility}',
                '"hidden"'::jsonb,
                true
            ),
            '{state_flags,hidden_from_players}',
            'true'::jsonb,
            true
        )
        WHERE entity_type = 'NPC'
          AND COALESCE((document->'state_flags'->>'hidden_from_players')::boolean, false)
        """
    )
    op.execute(
        """
        UPDATE campaign_entities ce
        SET document = jsonb_set(
            jsonb_set(
                document,
                '{state_flags,player_visibility}',
                '"unknown"'::jsonb,
                true
            ),
            '{state_flags,hidden_from_players}',
            'false'::jsonb,
            true
        )
        FROM scenes s
        WHERE ce.campaign_id = s.campaign_id
          AND s.status = 'ACTIVE'
          AND ce.entity_type = 'NPC'
          AND ce.id::text IN (
            SELECT jsonb_array_elements_text(s.scene_state->'context'->'hidden_npc_ids')
          )
          AND COALESCE(ce.document->'state_flags'->>'player_visibility', 'visible') <> 'hidden'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE campaign_entities
        SET document = document #- '{state_flags,player_visibility}'
        WHERE entity_type = 'NPC'
          AND document->'state_flags' ? 'player_visibility'
        """
    )

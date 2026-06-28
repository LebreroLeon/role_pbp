"""Persist scene chat messages outside scene_state JSONB.

Revision ID: 018
Revises: 017
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scene_messages",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_scene_messages_scene", "scene_messages", ["scene_id"])
    op.create_index(
        "idx_scene_messages_scene_created",
        "scene_messages",
        ["scene_id", "created_at"],
    )

    op.execute(
        """
        INSERT INTO scene_messages (id, scene_id, payload, created_at)
        SELECT
            COALESCE(NULLIF(elem->>'id', ''), 'legacy-' || s.id::text || '-' || ordinality::text),
            s.id,
            elem,
            COALESCE(
                NULLIF(elem->>'timestamp', '')::timestamptz,
                s.created_at
            )
        FROM scenes s
        CROSS JOIN LATERAL jsonb_array_elements(
            COALESCE(s.scene_state->'chat_buffer', '[]'::jsonb)
        ) WITH ORDINALITY AS t(elem, ordinality)
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("idx_scene_messages_scene_created", table_name="scene_messages")
    op.drop_index("idx_scene_messages_scene", table_name="scene_messages")
    op.drop_table("scene_messages")

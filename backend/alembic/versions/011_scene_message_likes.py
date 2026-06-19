"""Scene chat message likes.

Revision ID: 011
Revises: 010
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scene_message_likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scene_id", "message_id", "user_id", name="uq_scene_message_like"),
    )
    op.create_index("idx_scene_message_likes_scene", "scene_message_likes", ["scene_id"])
    op.create_index(
        "idx_scene_message_likes_message",
        "scene_message_likes",
        ["scene_id", "message_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_scene_message_likes_message", table_name="scene_message_likes")
    op.drop_index("idx_scene_message_likes_scene", table_name="scene_message_likes")
    op.drop_table("scene_message_likes")

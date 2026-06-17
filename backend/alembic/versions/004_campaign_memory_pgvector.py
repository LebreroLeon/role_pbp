"""Campaign memory table with pgvector embeddings.

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

memory_document_type = postgresql.ENUM(
    "CHAT_LOG",
    "WORLDLOG",
    "NPC_LORE",
    "SCENE_SUMMARY",
    name="memory_document_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        "CREATE TYPE memory_document_type AS ENUM ("
        "'CHAT_LOG', 'WORLDLOG', 'NPC_LORE', 'SCENE_SUMMARY'"
        ")"
    )

    op.create_table(
        "campaign_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", memory_document_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_memory_campaign", "campaign_memory", ["campaign_id"])
    op.execute(
        "CREATE INDEX idx_memory_embedding ON campaign_memory "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_memory_embedding")
    op.drop_index("idx_memory_campaign", table_name="campaign_memory")
    op.drop_table("campaign_memory")
    op.execute("DROP TYPE memory_document_type")

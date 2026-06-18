"""Semantic cache and campaign memory document types RULES/ADVENTURE.

Revision ID: 009
Revises: 008
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE memory_document_type ADD VALUE IF NOT EXISTS 'RULES'")
    op.execute("ALTER TYPE memory_document_type ADD VALUE IF NOT EXISTS 'ADVENTURE'")

    op.create_table(
        "semantic_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cache_key", sa.String(length=128), nullable=False),
        sa.Column("state_snapshot_hash", sa.Text(), nullable=False, server_default=""),
        sa.Column("query_embedding", Vector(1536), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "cache_key", name="uq_semantic_cache_campaign_key"),
    )
    op.create_index("idx_cache_campaign", "semantic_cache", ["campaign_id"])
    op.create_index("idx_cache_expires", "semantic_cache", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_cache_expires", table_name="semantic_cache")
    op.drop_index("idx_cache_campaign", table_name="semantic_cache")
    op.drop_table("semantic_cache")

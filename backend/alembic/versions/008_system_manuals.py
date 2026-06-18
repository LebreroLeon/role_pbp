"""System manual sources and vector memory for rulebook RAG.

Revision ID: 008
Revises: 007
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_manual_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("system_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_id", "filename", name="uq_system_manual_sources_system_filename"),
    )
    op.create_index("idx_system_manual_sources_system", "system_manual_sources", ["system_id"])

    op.create_table(
        "system_manual_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("system_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["system_manual_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_system_manual_memory_system", "system_manual_memory", ["system_id"])
    op.create_index("idx_system_manual_memory_source", "system_manual_memory", ["source_id"])
    op.execute(
        "CREATE INDEX idx_system_manual_memory_embedding ON system_manual_memory "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_system_manual_memory_embedding")
    op.drop_index("idx_system_manual_memory_source", table_name="system_manual_memory")
    op.drop_index("idx_system_manual_memory_system", table_name="system_manual_memory")
    op.drop_table("system_manual_memory")
    op.drop_index("idx_system_manual_sources_system", table_name="system_manual_sources")
    op.drop_table("system_manual_sources")

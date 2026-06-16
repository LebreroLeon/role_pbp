"""Campaign documents library and game_system field.

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("campaigns", sa.Column("game_system", sa.String(length=64), nullable=True))

    op.create_table(
        "campaign_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campaign_documents_campaign_id", "campaign_documents", ["campaign_id"])
    op.create_index("ix_campaign_documents_document_type", "campaign_documents", ["document_type"])


def downgrade() -> None:
    op.drop_index("ix_campaign_documents_document_type", table_name="campaign_documents")
    op.drop_index("ix_campaign_documents_campaign_id", table_name="campaign_documents")
    op.drop_table("campaign_documents")
    op.drop_column("campaigns", "game_system")

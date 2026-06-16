"""Users and campaign membership with roles.

Revision ID: 002
Revises: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

member_role = postgresql.ENUM("MASTER", "PLAYER", name="member_role", create_type=False)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE member_role AS ENUM ('MASTER', 'PLAYER');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "campaign_members",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", member_role, nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("campaign_id", "user_id"),
    )
    op.create_index("ix_campaign_members_user_id", "campaign_members", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_campaign_members_user_id", table_name="campaign_members")
    op.drop_table("campaign_members")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    member_role.drop(op.get_bind(), checkfirst=True)

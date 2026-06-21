import uuid

from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemMonsterCatalog(Base):
    __tablename__ = "system_monster_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    challenge_rating: Mapped[float] = mapped_column(Float, nullable=False)
    creature_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size: Mapped[str] = mapped_column(String(32), nullable=False)
    source_document: Mapped[str] = mapped_column(String(128), nullable=False)
    narrative_template: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sheet_template: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    raw_stat_block: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

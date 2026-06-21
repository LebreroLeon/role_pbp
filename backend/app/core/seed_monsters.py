"""Seed system_monster_catalog from vendored Open5e SRD snapshot."""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import create_db_engine
from app.models.monster_catalog import SystemMonsterCatalog
from app.rules.dnd5e.monster_sheet_mapper import (
    MonsterSheetMapper,
    build_narrative_template,
    normalize_monster_name,
    open5e_key_to_slug,
)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = _BACKEND_ROOT / "data" / "dnd5e" / "srd-monsters.json"
SYSTEM_ID = "dnd5e"


def load_snapshot(path: Path | None = None) -> list[dict]:
    snapshot_path = path or DEFAULT_SNAPSHOT
    if not snapshot_path.is_file():
        raise FileNotFoundError(f"SRD monster snapshot not found: {snapshot_path}")
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("SRD monster snapshot must be a JSON array")
    return data


def build_catalog_row(creature: dict) -> dict:
    key = str(creature.get("key") or creature.get("slug") or creature.get("name", ""))
    slug = open5e_key_to_slug(key)
    name = str(creature.get("name", slug))
    type_obj = creature.get("type") or {}
    size_obj = creature.get("size") or {}
    document = creature.get("document") or {}

    return {
        "id": uuid.uuid4(),
        "system_id": SYSTEM_ID,
        "slug": slug,
        "name": name,
        "name_normalized": normalize_monster_name(name),
        "challenge_rating": float(creature.get("challenge_rating") or 0),
        "creature_type": str(type_obj.get("name", "") if isinstance(type_obj, dict) else ""),
        "size": str(size_obj.get("name", "") if isinstance(size_obj, dict) else ""),
        "source_document": str(document.get("key", "srd-2014") if isinstance(document, dict) else "srd-2014"),
        "source_label": "SRD 5.1",
        "narrative_template": build_narrative_template(creature),
        "sheet_template": MonsterSheetMapper.map_creature(creature),
        "raw_stat_block": creature,
    }


async def upsert_monster_catalog(
    db: AsyncSession,
    *,
    snapshot_path: Path | None = None,
) -> int:
    creatures = load_snapshot(snapshot_path)
    count = 0
    for creature in creatures:
        if not isinstance(creature, dict):
            continue
        row = build_catalog_row(creature)
        stmt = (
            insert(SystemMonsterCatalog)
            .values(**row)
            .on_conflict_do_update(
                index_elements=["system_id", "slug"],
                set_={
                    "name": row["name"],
                    "name_normalized": row["name_normalized"],
                    "challenge_rating": row["challenge_rating"],
                    "creature_type": row["creature_type"],
                    "size": row["size"],
                    "source_document": row["source_document"],
                    "source_label": row["source_label"],
                    "narrative_template": row["narrative_template"],
                    "sheet_template": row["sheet_template"],
                    "raw_stat_block": row["raw_stat_block"],
                },
            )
        )
        await db.execute(stmt)
        count += 1
    await db.commit()
    return count


async def seed_monster_catalog_async(*, snapshot_path: Path | None = None) -> int:
    engine = create_db_engine(echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_maker() as db:
            return await upsert_monster_catalog(db, snapshot_path=snapshot_path)
    finally:
        await engine.dispose()


def seed_monster_catalog_if_enabled() -> None:
    """Run after migrations when SEED_MONSTERS is true. Never raises."""
    from app.core.config import settings

    mode = settings.seed_monsters_mode
    if mode is None:
        return

    try:
        total = asyncio.run(seed_monster_catalog_async())
        print(f"SEED_MONSTERS: finished ({total} monster(s) upserted).")
    except Exception as exc:
        print(f"SEED_MONSTERS: skipped due to error (non-fatal): {exc}", file=sys.stderr)


async def catalog_count(db: AsyncSession, *, system_id: str = SYSTEM_ID) -> int:
    rows = (
        await db.scalars(select(SystemMonsterCatalog.id).where(SystemMonsterCatalog.system_id == system_id))
    ).all()
    return len(rows)


def main() -> None:
    total = asyncio.run(seed_monster_catalog_async())
    print(f"Seeded {total} monsters into system_monster_catalog.")


if __name__ == "__main__":
    main()

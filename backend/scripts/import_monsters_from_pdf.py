"""Import monsters from local PDF manuals into system_monster_catalog.

LOCAL USE ONLY — do not run on Render or ship copyrighted stat blocks in the repo.
Requires DATABASE_URL in .env and the PDF on disk (not committed).

Usage (from repo root):
    cd backend
    python scripts/import_monsters_from_pdf.py --monster goblin --pdf "../data/manuals/dnd5e/manual-de-monstruos.pdf"
    python scripts/import_monsters_from_pdf.py --monster goblin --page 178 \\
        --pdf "C:/Users/you/Downloads/Dnd5/02D&D 5E - Manual de Monstruos (Edge).pdf"

The script upserts into system_monster_catalog with manual provenance (source_document,
source_label) and a sheet footer "Fuente: …".
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import unicodedata
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import create_db_engine
from app.models.monster_catalog import SystemMonsterCatalog
from app.rules.dnd5e.spanish_stat_block_parser import (
    build_catalog_row_from_parsed,
    extract_monster_block_from_page,
    extract_monster_lore_from_pages,
    parse_spanish_stat_block,
)
from app.services.system_manuals import extract_pdf_pages

SYSTEM_ID = "dnd5e"

MANUAL_SOURCES: dict[str, dict[str, str]] = {
    "mm-edge-es": {
        "source_document": "mm-edge-es",
        "source_label": "Manual de Monstruos (Edge)",
        "default_pdf_glob": "*Manual de Monstruos*Edge*.pdf",
    },
}

MONSTER_PRESETS: dict[str, dict[str, object]] = {
    "goblin": {
        "display_name": "Goblin",
        "page": 178,
        "slug_suffix": "mm-edge",
    },
}


def _normalize_monster_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def resolve_pdf_path(explicit: str | None, *, source_key: str) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {path}")
        return path

    repo_root = BACKEND_ROOT.parent
    manuals_dir = repo_root / "data" / "manuals" / SYSTEM_ID
    glob_pattern = str(MANUAL_SOURCES[source_key].get("default_pdf_glob", "*.pdf"))
    matches = sorted(manuals_dir.glob(glob_pattern), key=lambda p: p.name.lower())
    if not matches:
        raise FileNotFoundError(
            f"No PDF matching {glob_pattern!r} under {manuals_dir}. "
            "Pass --pdf with the full path to your local Manual de Monstruos."
        )
    return matches[0]


def extract_monster_from_pdf(
    pdf_path: Path,
    *,
    monster_key: str,
    page: int | None = None,
    source_key: str = "mm-edge-es",
) -> dict:
    preset = MONSTER_PRESETS.get(_normalize_monster_key(monster_key))
    if preset is None:
        known = ", ".join(sorted(MONSTER_PRESETS))
        raise ValueError(f"Unknown monster {monster_key!r}. Known presets: {known}")

    page_number = int(page or preset["page"])
    pages = extract_pdf_pages(pdf_path)
    page_map = dict(pages)
    if page_number not in page_map:
        raise ValueError(f"Page {page_number} not found in {pdf_path.name} ({len(pages)} pages)")

    block = extract_monster_block_from_page(page_map[page_number], str(preset["display_name"]))
    parsed = parse_spanish_stat_block(block)
    lore_text = extract_monster_lore_from_pages(
        page_map,
        stat_page=page_number,
        monster_name=str(preset["display_name"]),
    )
    source = MANUAL_SOURCES[source_key]
    slug = f"{_normalize_monster_key(str(preset['display_name']))}-{preset['slug_suffix']}"
    return build_catalog_row_from_parsed(
        parsed,
        slug=slug,
        source_document=source["source_document"],
        source_label=source["source_label"],
        system_id=SYSTEM_ID,
        lore_text=lore_text,
    )


async def upsert_catalog_row(row: dict) -> None:
    engine = create_db_engine(echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_maker() as db:
            stmt = (
                insert(SystemMonsterCatalog)
                .values(**row)
                .on_conflict_do_update(
                    index_elements=["system_id", "slug"],
                    set_={
                        key: row[key]
                        for key in row
                        if key not in {"id", "system_id", "slug"}
                    },
                )
            )
            await db.execute(stmt)
            await db.commit()
    finally:
        await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a monster stat block from a local PDF manual.")
    parser.add_argument("--monster", required=True, help="Monster preset key (e.g. goblin).")
    parser.add_argument("--pdf", default=None, help="Path to the PDF manual.")
    parser.add_argument("--page", type=int, default=None, help="Override PDF page number.")
    parser.add_argument(
        "--source",
        default="mm-edge-es",
        choices=sorted(MANUAL_SOURCES),
        help="Manual source key for provenance metadata.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse only; do not write to DB.")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    pdf_path = resolve_pdf_path(args.pdf, source_key=args.source)
    row = extract_monster_from_pdf(
        pdf_path,
        monster_key=args.monster,
        page=args.page,
        source_key=args.source,
    )
    print(f"Parsed {row['name']} from {pdf_path.name} (page {args.page or MONSTER_PRESETS[_normalize_monster_key(args.monster)]['page']})")
    print(f"  slug: {row['slug']}")
    print(f"  source_document: {row['source_document']}")
    print(f"  source_label: {row['source_label']}")
    print(f"  AC {row['sheet_template']['ac']} · HP avg {row['sheet_template']['hp']['max']} · CR {row['raw_stat_block']['parsed'].get('challenge_rating_display', row['challenge_rating'])}")
    lore_preview = row["raw_stat_block"].get("lore_text", "")
    if lore_preview:
        print(f"  lore: {lore_preview[:120]}{'…' if len(lore_preview) > 120 else ''}")

    if args.dry_run:
        print("Dry run — no database write.")
        return 0

    await upsert_catalog_row(row)
    print("Upserted into system_monster_catalog.")
    return 0


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(run(args))
    except Exception as exc:
        print(f"import_monsters_from_pdf failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

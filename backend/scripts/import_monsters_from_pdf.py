"""Import monsters from local PDF manuals into system_monster_catalog.

LOCAL USE ONLY — do not run on Render or ship copyrighted stat blocks in the repo.
Requires DATABASE_URL in .env and the PDF on disk (not committed).

Usage (from repo root):
    cd backend
    python scripts/import_monsters_from_pdf.py --monster goblin
    python scripts/import_monsters_from_pdf.py --monster goblin --pdf "../data/manuals/dnd5e/manual-de-monstruos.pdf"
    python scripts/import_monsters_from_pdf.py --list-index --source mm-edge-es
    python scripts/import_monsters_from_pdf.py --from-index --source mm-edge-es --limit 5 --dry-run
    python scripts/import_monsters_from_pdf.py --from-index --source mm-edge-es --report /tmp/import-report.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
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
from app.rules.dnd5e.pdf_monster_index import (
    MonsterIndexEntry,
    build_monster_index,
    index_entry_slug,
    resolve_index_entry,
)
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
        "slug_suffix": "mm-edge",
    },
    "volo-edge-es": {
        "source_document": "volo-edge-es",
        "source_label": "Guía de Monstruos de Volo (Edge)",
        "default_pdf_glob": "*Monstruos de Volo*.pdf",
        "slug_suffix": "volo-edge",
    },
    "multiverse-edge-es": {
        "source_document": "multiverse-edge-es",
        "source_label": "Monstruos del Multiverso (Edge)",
        "default_pdf_glob": "*Multiverso*.pdf",
        "slug_suffix": "multiverse-edge",
    },
}

MONSTER_PRESETS: dict[str, dict[str, object]] = {
    "goblin": {
        "display_name": "Goblin",
        "page": 178,
        "slug_suffix": "mm-edge",
        "source_key": "mm-edge-es",
    },
    "neothelido": {
        "display_name": "NEOTHELIDO",
        "page": 177,
        "slug_suffix": "volo-edge",
        "source_key": "volo-edge-es",
    },
    "oblex-anciano": {
        "display_name": "OBLEX ANCIANO",
        "page": 213,
        "slug_suffix": "multiverse-edge",
        "source_key": "multiverse-edge-es",
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
            "Pass --pdf with the full path to your local manual."
        )
    return matches[0]


def _source_meta(source_key: str) -> dict[str, str]:
    if source_key not in MANUAL_SOURCES:
        raise ValueError(f"Unknown source {source_key!r}")
    return MANUAL_SOURCES[source_key]


def extract_monster_from_pdf(
    pdf_path: Path,
    *,
    monster_name: str,
    page: int,
    source_key: str,
    slug_suffix: str | None = None,
) -> dict:
    source = _source_meta(source_key)
    page_number = int(page)
    pages = extract_pdf_pages(pdf_path)
    page_map = dict(pages)
    if page_number not in page_map:
        raise ValueError(f"Page {page_number} not found in {pdf_path.name} ({len(pages)} pages)")

    block = extract_monster_block_from_page(page_map[page_number], monster_name)
    parsed = parse_spanish_stat_block(block)
    lore_text = extract_monster_lore_from_pages(
        page_map,
        stat_page=page_number,
        monster_name=monster_name,
    )
    suffix = slug_suffix or source.get("slug_suffix", "edge")
    slug = f"{_normalize_monster_key(monster_name)}-{suffix}"
    return build_catalog_row_from_parsed(
        parsed,
        slug=slug,
        source_document=source["source_document"],
        source_label=source["source_label"],
        system_id=SYSTEM_ID,
        lore_text=lore_text,
    )


def extract_monster_from_index_entry(
    pdf_path: Path,
    entry: MonsterIndexEntry,
    *,
    source_key: str,
) -> dict:
    source = _source_meta(source_key)
    return extract_monster_from_pdf(
        pdf_path,
        monster_name=entry.name,
        page=entry.page,
        source_key=source_key,
        slug_suffix=source.get("slug_suffix"),
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


def _summary_line(row: dict) -> str:
    sheet = row["sheet_template"]
    cr = row["raw_stat_block"]["parsed"].get("challenge_rating_display", row["challenge_rating"])
    attacks = len(sheet.get("attacks") or [])
    features = row["sheet_template"].get("features_traits") or ""
    has_spells = "--- Hechizos ---" in features
    page = row["raw_stat_block"].get("page", "?")
    return (
        f"  {row['name']} (p.{page}) · "
        f"AC {sheet['ac']} · HP {sheet['hp']['max']} · CR {cr} · "
        f"{attacks} ataque(s) · hechizos={'sí' if has_spells else 'no'}"
    )


def run_batch_import(
    pdf_path: Path,
    *,
    source_key: str,
    limit: int | None,
    dry_run: bool,
    report_path: Path | None,
) -> int:
    index = build_monster_index(pdf_path)
    if not index:
        print(f"No index entries found in {pdf_path.name}", file=sys.stderr)
        return 1

    entries = index[:limit] if limit else index
    print(f"Index: {len(index)} entries ({index[0].source} primary); processing {len(entries)}")

    results: list[dict[str, object]] = []
    failures = 0
    successes = 0

    for entry in entries:
        record: dict[str, object] = {
            "name": entry.name,
            "page": entry.page,
            "index_source": entry.source,
            "status": "pending",
        }
        try:
            row = extract_monster_from_index_entry(pdf_path, entry, source_key=source_key)
            row["raw_stat_block"]["page"] = entry.page
            record["status"] = "ok"
            record["slug"] = row["slug"]
            record["cr"] = row["raw_stat_block"]["parsed"].get("challenge_rating_display", row["challenge_rating"])
            record["ac"] = row["sheet_template"]["ac"]
            record["hp"] = row["sheet_template"]["hp"]["max"]
            record["attacks"] = len(row["sheet_template"].get("attacks") or [])
            record["has_spells"] = "--- Hechizos ---" in (row["sheet_template"].get("features_traits") or "")
            print(_summary_line(row))
            if not dry_run:
                asyncio.run(upsert_catalog_row(row))
            successes += 1
        except Exception as exc:
            record["status"] = "error"
            record["error"] = str(exc)
            failures += 1
            print(f"  FAIL {entry.name} (p.{entry.page}): {exc}", file=sys.stderr)
        results.append(record)

    print(f"Done: {successes} ok, {failures} failed (dry_run={dry_run})")
    if report_path:
        report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report written to {report_path}")
    return 0 if failures == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import monster stat blocks from local PDF manuals.")
    parser.add_argument("--monster", default=None, help="Monster preset key or index name (e.g. goblin).")
    parser.add_argument("--pdf", default=None, help="Path to the PDF manual.")
    parser.add_argument("--page", type=int, default=None, help="Override PDF page number.")
    parser.add_argument(
        "--source",
        default=None,
        choices=sorted(MANUAL_SOURCES),
        help="Manual source key for provenance metadata.",
    )
    parser.add_argument("--list-index", action="store_true", help="Print monster index and exit.")
    parser.add_argument("--from-index", action="store_true", help="Import all monsters found in the PDF index.")
    parser.add_argument("--limit", type=int, default=None, help="Max monsters to process in batch mode.")
    parser.add_argument("--report", default=None, help="Write JSON report path for batch imports.")
    parser.add_argument("--dry-run", action="store_true", help="Parse only; do not write to DB.")
    return parser.parse_args()


async def run_single(args: argparse.Namespace) -> int:
    if not args.monster:
        raise ValueError("--monster is required unless using --from-index or --list-index")

    preset = MONSTER_PRESETS.get(_normalize_monster_key(args.monster))
    source_key = args.source or (str(preset.get("source_key")) if preset else None) or "mm-edge-es"
    pdf_path = resolve_pdf_path(args.pdf, source_key=source_key)

    if args.page is not None:
        page = args.page
        display_name = str(preset["display_name"]) if preset else args.monster
    elif preset:
        page = int(preset["page"])
        display_name = str(preset["display_name"])
    else:
        index = build_monster_index(pdf_path)
        entry = resolve_index_entry(index, args.monster)
        if entry is None:
            raise ValueError(f"Monster {args.monster!r} not found in PDF index ({len(index)} entries)")
        page = entry.page
        display_name = entry.name
        print(f"Resolved from index ({entry.source}): {entry.name} → page {entry.page}")

    row = extract_monster_from_pdf(
        pdf_path,
        monster_name=display_name,
        page=page,
        source_key=source_key,
        slug_suffix=str(preset.get("slug_suffix")) if preset else None,
    )
    row["raw_stat_block"]["page"] = page
    print(f"Parsed {row['name']} from {pdf_path.name} (page {page})")
    print(f"  slug: {row['slug']}")
    print(_summary_line(row))

    if args.dry_run:
        print("Dry run — no database write.")
        return 0

    await upsert_catalog_row(row)
    print("Upserted into system_monster_catalog.")
    return 0


def main() -> int:
    args = parse_args()
    try:
        source_key = args.source or "mm-edge-es"
        if args.list_index or args.from_index:
            pdf_path = resolve_pdf_path(args.pdf, source_key=source_key)
            if args.list_index:
                index = build_monster_index(pdf_path)
                print(f"{len(index)} entries in {pdf_path.name} (primary: {index[0].source if index else 'n/a'})")
                for entry in index:
                    slug = index_entry_slug(entry, suffix=_source_meta(source_key)["slug_suffix"])
                    print(f"  p.{entry.page:>4}  {entry.name:<40}  [{entry.source}]  {slug}")
                return 0
            report_path = Path(args.report).expanduser() if args.report else None
            return run_batch_import(
                pdf_path,
                source_key=source_key,
                limit=args.limit,
                dry_run=args.dry_run,
                report_path=report_path,
            )
        return asyncio.run(run_single(args))
    except Exception as exc:
        print(f"import_monsters_from_pdf failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

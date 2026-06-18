"""Index official game-system PDFs from data/manuals/{system_id}/ into vector memory.

Usage (from repo root):
    cd backend
    python scripts/index_system_manuals.py --system dnd5e
    python scripts/index_system_manuals.py --system dnd5e --dry-run
    python scripts/index_system_manuals.py --all --force

Requires: pymupdf, OPENAI_API_KEY, migration 008 (system_manual_* tables).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings
from app.core.database import SessionLocal
from app.rules.game_systems import GAME_SYSTEM_PROFILES
from app.services.system_manuals import fetch_sources_by_system, index_system_manual_pdf, list_pdfs

VALID_SYSTEM_IDS = frozenset(GAME_SYSTEM_PROFILES.keys())


def resolve_manuals_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return Path(settings.system_manuals_dir).expanduser().resolve()


async def scan_system(
    db,
    system_id: str,
    manuals_root: Path,
    *,
    dry_run: bool,
    force: bool,
) -> int:
    system_dir = manuals_root / system_id
    pdfs = list_pdfs(system_dir)

    print(f"\n[{system_id}] {system_dir}")
    if not pdfs:
        print("  (sin PDFs — copia manuales según data/manuals/{}/README.md)".format(system_id))
        return 0

    total_chunks = 0
    sources = await fetch_sources_by_system(db, system_id)

    for pdf in pdfs:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"  {pdf.name} ({size_mb:.1f} MB)")

        existing = sources.get(pdf.name)
        if existing and existing.indexed_at is not None and not force and not dry_run:
            print(f"    → SKIP (already indexed, {existing.chunk_count} chunks)")
            continue

        try:
            chunk_count = await index_system_manual_pdf(
                db,
                system_id=system_id,
                pdf_path=pdf,
                manuals_root=manuals_root,
                force=force,
                dry_run=dry_run,
            )
        except RuntimeError as exc:
            print(f"    → ABORT ({exc})")
            return total_chunks

        if dry_run:
            action = f"DRY-RUN ({chunk_count} chunks)" if chunk_count else "SKIP (no text)"
        elif chunk_count == 0:
            action = "SKIP (no extractable text)"
        else:
            action = f"INDEXED ({chunk_count} chunks)"

        print(f"    → {action}")
        total_chunks += chunk_count

    print(f"  Total: {len(pdfs)} PDF(s), {total_chunks} chunk(s) processed.")
    return total_chunks


async def run(args: argparse.Namespace) -> int:
    manuals_root = resolve_manuals_dir(args.manuals_dir)
    if not manuals_root.is_dir():
        print(f"Error: manuals directory not found: {manuals_root}", file=sys.stderr)
        return 1

    systems = sorted(VALID_SYSTEM_IDS) if args.all else [args.system]
    total_chunks = 0

    async with SessionLocal() as db:
        for system_id in systems:
            total_chunks += await scan_system(
                db,
                system_id,
                manuals_root,
                dry_run=args.dry_run,
                force=args.force,
            )

    print(f"\nDone. {total_chunks} chunk(s) processed.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index system rulebook PDFs for RAG.")
    parser.add_argument(
        "--system",
        choices=sorted(VALID_SYSTEM_IDS),
        help="Game system id (dnd5e, vtm_v5, cyberpunk_red).",
    )
    parser.add_argument("--all", action="store_true", help="Scan every known system_id.")
    parser.add_argument(
        "--manuals-dir",
        default=None,
        help="Override manuals root (default: SYSTEM_MANUALS_DIR / data/manuals).",
    )
    parser.add_argument("--dry-run", action="store_true", help="List files and chunk counts only; no DB writes.")
    parser.add_argument("--force", action="store_true", help="Re-index even if already indexed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.all and not args.system:
        print("Error: specify --system <id> or --all", file=sys.stderr)
        return 2
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())

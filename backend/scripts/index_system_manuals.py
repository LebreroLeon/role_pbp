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

from app.core.seed_manuals import VALID_SYSTEM_IDS, resolve_manuals_dir, seed_system_manuals


async def run(args: argparse.Namespace) -> int:
    manuals_root = resolve_manuals_dir(args.manuals_dir)
    if not manuals_root.is_dir():
        print(f"Error: manuals directory not found: {manuals_root}", file=sys.stderr)
        return 1

    systems = sorted(VALID_SYSTEM_IDS) if args.all else [args.system]
    total_chunks = await seed_system_manuals(
        manuals_dir=manuals_root,
        systems=systems,
        force=args.force,
        dry_run=args.dry_run,
        skip_if_indexed=False,
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

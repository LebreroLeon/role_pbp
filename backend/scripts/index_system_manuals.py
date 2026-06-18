"""Index official game-system PDFs from data/manuals/{system_id}/ into vector memory.

Stub — full pipeline described in docs/07_system_manuals.md.

Usage (from repo root):
    cd backend
    python scripts/index_system_manuals.py --system dnd5e
    python scripts/index_system_manuals.py --system dnd5e --dry-run
    python scripts/index_system_manuals.py --all --force

Requires (future): pymupdf or pdfplumber, OPENAI_API_KEY, migrations for
system_manual_sources + system_manual_memory tables.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

VALID_SYSTEM_IDS = frozenset({"dnd5e", "vtm_v5", "cyberpunk_red"})
DEFAULT_MANUALS_DIR = REPO_ROOT / "data" / "manuals"


def resolve_manuals_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_MANUALS_DIR.resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_pdfs(system_dir: Path) -> list[Path]:
    if not system_dir.is_dir():
        return []
    return sorted(system_dir.glob("*.pdf"), key=lambda p: p.name.lower())


def scan_system(system_id: str, manuals_root: Path, *, dry_run: bool) -> int:
    system_dir = manuals_root / system_id
    pdfs = list_pdfs(system_dir)

    print(f"\n[{system_id}] {system_dir}")
    if not pdfs:
        print("  (sin PDFs — copia manuales según data/manuals/{}/README.md)".format(system_id))
        return 0

    for pdf in pdfs:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        file_hash = sha256_file(pdf)
        action = "SKIP (stub)" if dry_run else "SKIP (stub — indexación no implementada)"
        print(f"  - {pdf.name} ({size_mb:.1f} MB) sha256={file_hash[:12]}… → {action}")

    print(f"  Total: {len(pdfs)} PDF(s). Implementar extracción + embeddings en system_manual_memory.")
    return len(pdfs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index system rulebook PDFs for RAG (stub).")
    parser.add_argument(
        "--system",
        choices=sorted(VALID_SYSTEM_IDS),
        help="Game system id (dnd5e, vtm_v5, cyberpunk_red).",
    )
    parser.add_argument("--all", action="store_true", help="Scan every known system_id.")
    parser.add_argument(
        "--manuals-dir",
        default=None,
        help=f"Override manuals root (default: {DEFAULT_MANUALS_DIR}).",
    )
    parser.add_argument("--dry-run", action="store_true", help="List files only; no DB writes.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-index even if sha256 unchanged (no-op until pipeline exists).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.all and not args.system:
        print("Error: specify --system <id> or --all", file=sys.stderr)
        return 2

    manuals_root = resolve_manuals_dir(args.manuals_dir)
    if not manuals_root.is_dir():
        print(f"Error: manuals directory not found: {manuals_root}", file=sys.stderr)
        return 1

    systems = sorted(VALID_SYSTEM_IDS) if args.all else [args.system]
    total = 0
    for system_id in systems:
        total += scan_system(system_id, manuals_root, dry_run=args.dry_run)

    if args.force:
        print("\n--force: sin efecto hasta implementar borrado/re-indexación de chunks.")

    print(f"\nDone. {total} PDF(s) encontrados. Ver docs/07_system_manuals.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

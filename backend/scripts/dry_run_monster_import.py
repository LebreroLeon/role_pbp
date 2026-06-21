"""Batch dry-run for Spanish PDF monster import with summary report.

Usage:
    cd backend
    python scripts/dry_run_monster_import.py --source mm-edge-es \\
        --pdf "../data/manuals/dnd5e/manual-de-monstruos.pdf"
    python scripts/dry_run_monster_import.py --fixtures-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = BACKEND_ROOT / "data" / "monster-import-dry-run.json"


def run_fixtures_only() -> int:
    fixtures_script = BACKEND_ROOT / "scripts" / "_dry_run_fixtures.py"
    result = subprocess.run([sys.executable, str(fixtures_script)], check=False)
    return result.returncode


def summarize_report(report_path: Path) -> None:
    if not report_path.is_file():
        print(f"Report not found: {report_path}", file=sys.stderr)
        return

    rows = json.loads(report_path.read_text(encoding="utf-8"))
    total = len(rows)
    ok = [row for row in rows if row.get("status") == "ok"]
    failed = [row for row in rows if row.get("status") != "ok"]
    spells = sum(1 for row in ok if row.get("has_spells"))
    multi_section = sum(
        1
        for row in ok
        if isinstance(row.get("action_sections"), list) and len(row["action_sections"]) > 1
    )

    print("\n=== Resumen dry-run ===")
    print(f"Total:     {total}")
    print(f"OK:        {len(ok)} ({(len(ok) / total * 100):.1f}%)" if total else "OK:        0")
    print(f"Fallos:    {len(failed)}")
    print(f"Con hechizos: {spells}")
    if failed:
        reasons = Counter(str(row.get("error", "unknown"))[:80] for row in failed)
        print("\nErrores frecuentes:")
        for reason, count in reasons.most_common(8):
            print(f"  {count:>4}x  {reason}")

    if ok:
        print("\nMuestra OK (primeros 15):")
        for row in ok[:15]:
            print(
                f"  p.{row.get('page', '?'):>4}  {row.get('name', '?'):<32} "
                f"CR {row.get('cr', '?'):<4} atk={row.get('attacks', 0)} "
                f"spells={'sí' if row.get('has_spells') else 'no'}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run batch monster import with summary.")
    parser.add_argument("--source", default="mm-edge-es", help="Manual source key.")
    parser.add_argument("--pdf", default=None, help="Path to PDF manual.")
    parser.add_argument("--limit", type=int, default=None, help="Max monsters to process.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="JSON report output path.")
    parser.add_argument("--fixtures-only", action="store_true", help="Run only fixture subset (no PDF).")
    args = parser.parse_args()

    if args.fixtures_only:
        return run_fixtures_only()

    import_script = BACKEND_ROOT / "scripts" / "import_monsters_from_pdf.py"
    cmd = [
        sys.executable,
        str(import_script),
        "--from-index",
        "--source",
        args.source,
        "--dry-run",
        "--report",
        args.report,
    ]
    if args.pdf:
        cmd.extend(["--pdf", args.pdf])
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])

    print("Ejecutando:", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    summarize_report(Path(args.report))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

"""Internal: dry-run monster parse on committed fixtures (no PDF required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.rules.dnd5e.spanish_stat_block_parser import (
    build_catalog_row_from_parsed,
    extract_monster_block_from_page,
    extract_monster_lore_from_pages,
    parse_spanish_stat_block,
    validate_parsed_sheet,
)

FIXTURES = BACKEND / "tests" / "fixtures"
REPORT = BACKEND / "data" / "mm-edge-fixture-dry-run.json"

SOURCES = {
    "mm-edge-es": ("Manual de Monstruos (Edge)", "mm-edge"),
    "volo-edge-es": ("Guía de Monstruos de Volo (Edge)", "volo-edge"),
    "multiverse-edge-es": ("Monstruos del Multiverso (Edge)", "multiverse-edge"),
}

CASES = [
    {
        "key": "goblin",
        "source": "mm-edge-es",
        "mode": "page",
        "page_file": "goblin_mm_edge_page178.txt",
        "lore_files": {177: "goblin_mm_edge_page177.txt"},
        "monster_name": "Goblin",
        "page": 178,
    },
    {
        "key": "neothelido",
        "source": "volo-edge-es",
        "mode": "block",
        "block_file": "neothelido_volo_page177.txt",
        "page": 177,
    },
    {
        "key": "oblex-anciano",
        "source": "multiverse-edge-es",
        "mode": "block",
        "block_file": "oblex_anciano_multiverse_page213.txt",
        "page": 213,
    },
]


def main() -> int:
    results: list[dict] = []
    for case in CASES:
        source_label, slug_suffix = SOURCES[case["source"]]
        record: dict = {
            "key": case["key"],
            "source": case["source"],
            "page": case.get("page"),
            "status": "pending",
        }
        try:
            if case["mode"] == "page":
                page_text = (FIXTURES / case["page_file"]).read_text(encoding="utf-8")
                block = extract_monster_block_from_page(page_text, case["monster_name"])
                pages = {case["page"]: page_text}
                for page_num, filename in case.get("lore_files", {}).items():
                    pages[page_num] = (FIXTURES / filename).read_text(encoding="utf-8")
                lore = extract_monster_lore_from_pages(
                    pages,
                    stat_page=case["page"],
                    monster_name=case["monster_name"],
                )
                parsed = parse_spanish_stat_block(block)
            else:
                block = (FIXTURES / case["block_file"]).read_text(encoding="utf-8")
                parsed = parse_spanish_stat_block(block)
                lore = ""

            sheet = validate_parsed_sheet(parsed, source_label=source_label)
            build_catalog_row_from_parsed(
                parsed,
                slug=f"{case['key']}-{slug_suffix}",
                source_document=case["source"],
                source_label=source_label,
                lore_text=lore,
            )
            record.update(
                {
                    "status": "ok",
                    "name": parsed.name,
                    "cr": parsed.challenge_rating_raw,
                    "ac": sheet.ac,
                    "hp": sheet.hp.max,
                    "attacks": len(sheet.attacks),
                    "has_spells": "--- Hechizos ---" in sheet.features_traits,
                    "action_sections": sorted({a.get("section", "actions") for a in parsed.actions}),
                }
            )
        except Exception as exc:
            record["status"] = "error"
            record["error"] = str(exc)
        results.append(record)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for row in results if row["status"] == "ok")
    print(f"Fixture dry-run: {ok}/{len(results)} OK → {REPORT}")
    for row in results:
        if row["status"] == "ok":
            print(
                f"  OK  {row['name']:<18} CR {row['cr']:<4} "
                f"atk={row['attacks']} spells={'sí' if row['has_spells'] else 'no'}"
            )
        else:
            print(f"  FAIL {row['key']}: {row['error']}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

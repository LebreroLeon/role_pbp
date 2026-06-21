"""Fetch Open5e SRD 2014 creatures and vendorize to backend/data/dnd5e/srd-monsters.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = BACKEND_ROOT / "data" / "dnd5e" / "srd-monsters.json"
OPEN5E_LIST_URL = "https://api.open5e.com/v2/creatures/"
DOCUMENT_KEY = "srd-2014"
PAGE_SIZE = 50


def fetch_all_srd_monsters() -> list[dict]:
    results: list[dict] = []
    url: str | None = f"{OPEN5E_LIST_URL}?document__key={DOCUMENT_KEY}&limit={PAGE_SIZE}"
    with httpx.Client(timeout=120.0, headers={"User-Agent": "RolePBP/1.0"}) as client:
        while url:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
            batch = payload.get("results", [])
            if not isinstance(batch, list):
                raise RuntimeError("Unexpected Open5e response shape")
            results.extend(batch)
            url = payload.get("next")
    return results


def main() -> None:
    monsters = fetch_all_srd_monsters()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(monsters, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(monsters)} monsters to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"fetch_srd_monsters failed: {exc}", file=sys.stderr)
        sys.exit(1)

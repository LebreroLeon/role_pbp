"""Backfill campaigns.game_system to dnd5e and align PC system_mechanics.system_id with the campaign."""

from __future__ import annotations

import argparse
import asyncio
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import ValidationError
from sqlalchemy import select\r\n
from app.core.database import SessionLocal
from app.models.campaign import Campaign, CampaignEntity
from app.rules.registry import get_plugin

VALID_GAME_SYSTEMS = frozenset({"dnd5e", "cyberpunk_red", "vtm_v5"})
DEFAULT_GAME_SYSTEM = "dnd5e"


def _display_game_system(value: str | None) -> str:
    if value is None or not str(value).strip():
        return "(null/empty)"
    return str(value)


def needs_game_system_fix(value: str | None) -> bool:
    if value is None:
        return True
    trimmed = value.strip()
    if not trimmed:
        return True
    return trimmed not in VALID_GAME_SYSTEMS


def normalize_pc_sheet(campaign_game_system: str, sheet: Any) -> dict[str, Any]:
    plugin = get_plugin(campaign_game_system)
    base_sheet = deepcopy(sheet) if isinstance(sheet, dict) else {}
    try:
        validated = plugin.validate_pc_sheet(base_sheet)
    except ValidationError:
        return plugin.default_pc_sheet()
    if hasattr(validated, "model_dump"):
        return validated.model_dump(mode="json")
    if isinstance(validated, dict):
        return validated
    raise TypeError("validate_pc_sheet must return dict or BaseModel")


async def run(*, dry_run: bool) -> int:
    campaign_changes: list[tuple[str, str, str, str]] = []
    pc_changes: list[tuple[str, str, str, str, str]] = []

    async with SessionLocal() as db:
        campaigns = (await db.execute(select(Campaign))).scalars().all()
        campaign_by_id = {c.id: c for c in campaigns}

        for campaign in campaigns:
            before = campaign.game_system
            if not needs_game_system_fix(before):
                continue
            after = DEFAULT_GAME_SYSTEM
            campaign_changes.append(
                (str(campaign.id), campaign.name, _display_game_system(before), after)
            )
            if not dry_run:
                campaign.game_system = after

        entities = (
            await db.execute(
                select(CampaignEntity).where(CampaignEntity.entity_type == "PC")
            )
        ).scalars().all()

        for entity in entities:
            campaign = campaign_by_id.get(entity.campaign_id)
            if campaign is None:
                continue
            target_system = campaign.game_system
            if not target_system or needs_game_system_fix(target_system):
                target_system = DEFAULT_GAME_SYSTEM
            plugin = get_plugin(target_system)
            expected_system_id = plugin.system_id

            document = deepcopy(entity.document) if isinstance(entity.document, dict) else {}
            mechanics = document.get("system_mechanics")
            if not isinstance(mechanics, dict):
                mechanics = {}
            current_system_id = mechanics.get("system_id")
            current_sheet = mechanics.get("sheet")

            needs_pc_fix = current_system_id != expected_system_id
            normalized_sheet = normalize_pc_sheet(target_system, current_sheet)
            if current_sheet != normalized_sheet:
                needs_pc_fix = True

            if not needs_pc_fix:
                continue

            pc_name = (
                document.get("identity", {}).get("name")
                if isinstance(document.get("identity"), dict)
                else None
            )
            pc_changes.append(
                (
                    str(entity.id),
                    pc_name or "(unnamed)",
                    str(entity.campaign_id),
                    str(current_system_id),
                    expected_system_id,
                )
            )
            if not dry_run:
                mechanics["system_id"] = expected_system_id
                profile = getattr(plugin, "sheet_schema_version", None)
                if profile:
                    mechanics["schema_version"] = plugin.sheet_schema_version
                mechanics["sheet"] = normalized_sheet
                document["system_mechanics"] = mechanics
                entity.document = document

        if dry_run:
            await db.rollback()
        else:
            await db.commit()

    print("=== Campaigns ===")
    if not campaign_changes:
        print("No campaign game_system updates needed.")
    else:
        for cid, name, before, after in campaign_changes:
            print(f"  {cid} | {name!r} | {before} -> {after}")

    print("=== PCs (system_mechanics.system_id) ===")
    if not pc_changes:
        print("No PC system_id updates needed.")
    else:
        for eid, pc_name, camp_id, before, after in pc_changes:
            print(
                f"  {eid} | {pc_name!r} | campaign={camp_id} | {before!r} -> {after!r}"
            )

    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n{mode}: {len(campaign_changes)} campaign(s), {len(pc_changes)} PC(s).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill campaign game_system and PC system_mechanics.system_id."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without committing.",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(dry_run=args.dry_run)))


if __name__ == "__main__":
    main()


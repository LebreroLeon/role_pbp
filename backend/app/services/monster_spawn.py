"""Spawn NPCs from the system monster catalog."""

from __future__ import annotations

import re
import uuid
from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import CampaignEntity
from app.models.monster_catalog import SystemMonsterCatalog
from app.schemas.entities import EntityType
from app.services.entities import (
    EntityValidationError,
    get_campaign_or_error,
    normalize_entity_document_for_campaign,
    validate_entity_cross_references,
    validate_entity_document,
)


class MonsterCatalogError(ValueError):
    pass


def _next_monster_names(base_name: str, existing_names: list[str], count: int) -> list[str]:
    used_numbers: set[int] = set()
    pattern = re.compile(rf"^{re.escape(base_name)}\s+(\d+)$", re.IGNORECASE)
    for name in existing_names:
        match = pattern.match(name.strip())
        if match:
            used_numbers.add(int(match.group(1)))

    names: list[str] = []
    number = 1
    while len(names) < count:
        if number not in used_numbers:
            names.append(f"{base_name} {number}")
        number += 1
    return names


async def _existing_npc_names(db: AsyncSession, campaign_id: uuid.UUID) -> list[str]:
    npcs = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.entity_type == EntityType.NPC.value,
            )
        )
    ).all()
    names: list[str] = []
    for npc in npcs:
        identity = npc.document.get("identity")
        if isinstance(identity, dict):
            name = identity.get("name")
            if isinstance(name, str):
                names.append(name)
    return names


async def get_catalog_monster(
    db: AsyncSession,
    *,
    system_id: str,
    slug: str,
) -> SystemMonsterCatalog | None:
    return await db.scalar(
        select(SystemMonsterCatalog).where(
            SystemMonsterCatalog.system_id == system_id,
            SystemMonsterCatalog.slug == slug,
        )
    )


async def search_catalog_monsters(
    db: AsyncSession,
    *,
    system_id: str,
    query: str | None = None,
    limit: int = 20,
) -> list[SystemMonsterCatalog]:
    stmt = select(SystemMonsterCatalog).where(SystemMonsterCatalog.system_id == system_id)
    if query and query.strip():
        normalized = re.sub(r"[\s_-]+", "", query.strip().lower())
        stmt = stmt.where(SystemMonsterCatalog.name_normalized.contains(normalized))
    stmt = stmt.order_by(SystemMonsterCatalog.name).limit(max(1, min(limit, 100)))
    return list((await db.scalars(stmt)).all())


def build_npc_document_from_catalog(
    catalog_entry: SystemMonsterCatalog,
    *,
    name: str,
    player_visibility: str = "hidden",
    attitude: str = "hostile",
) -> dict:
    narrative = deepcopy(catalog_entry.narrative_template or {})
    sheet = deepcopy(catalog_entry.sheet_template or {})

    return {
        "metadata": {
            "type": "NPC",
            "system_agnostic": False,
            "mechanics_enabled": True,
            "version": "2.0.0",
        },
        "identity": {
            "name": name,
            "concept": str(narrative.get("concept", catalog_entry.name)),
            "faction_id": None,
            "current_location_id": None,
        },
        "ai_narrative_profile": {
            "public_description": str(narrative.get("public_description", "")),
            "secret_lore_master": str(narrative.get("secret_lore_master", "")),
            "personality_traits": list(narrative.get("personality_traits") or ["hostil"]),
            "voice_and_tone": str(narrative.get("voice_and_tone", "Amenazante")),
        },
        "system_mechanics": {
            "system_id": catalog_entry.system_id,
            "schema_version": "1.0.0",
            "sheet": sheet,
        },
        "state_flags": {
            "is_dead": False,
            "is_present_in_scene": False,
            "attitude_towards_party": attitude,
            "has_met_party": False,
            "player_visibility": player_visibility,
            "hidden_from_players": player_visibility == "hidden",
        },
    }


async def spawn_monsters(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    slug: str,
    count: int,
    player_visibility: str = "hidden",
    attitude: str = "hostile",
    system_id: str = "dnd5e",
) -> list[CampaignEntity]:
    if count < 1 or count > 50:
        raise MonsterCatalogError("count must be between 1 and 50")
    if player_visibility not in ("hidden", "unknown", "visible"):
        raise MonsterCatalogError("player_visibility must be hidden, unknown, or visible")

    campaign = await get_campaign_or_error(db, campaign_id)
    if campaign.game_system != system_id:
        raise MonsterCatalogError(f"Campaign game system must be {system_id!r}")

    catalog_entry = await get_catalog_monster(db, system_id=system_id, slug=slug)
    if catalog_entry is None:
        raise MonsterCatalogError(f"Monster {slug!r} not found in catalog")

    existing_names = await _existing_npc_names(db, campaign_id)
    names = _next_monster_names(catalog_entry.name, existing_names, count)
    created: list[CampaignEntity] = []

    for name in names:
        document = build_npc_document_from_catalog(
            catalog_entry,
            name=name,
            player_visibility=player_visibility,
            attitude=attitude,
        )
        try:
            normalized = normalize_entity_document_for_campaign(
                campaign_game_system=campaign.game_system,
                entity_type=EntityType.NPC,
                document=document,
            )
            validated = validate_entity_document(EntityType.NPC, normalized)
            document_json = validated.model_dump(mode="json")
            await validate_entity_cross_references(
                db,
                campaign_id=campaign_id,
                entity_type=EntityType.NPC,
                document=document_json,
            )
        except EntityValidationError as exc:
            raise MonsterCatalogError(str(exc)) from exc

        entity = CampaignEntity(
            campaign_id=campaign_id,
            entity_type=EntityType.NPC.value,
            document=document_json,
        )
        db.add(entity)
        created.append(entity)

    await db.commit()
    for entity in created:
        await db.refresh(entity)
    return created

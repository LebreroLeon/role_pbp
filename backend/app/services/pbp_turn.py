"""Play-by-post turn order and enforcement.

When ``turn_management.pbp_enabled`` is true, only the current turn holder may post
(players). The master always bypasses turn checks. Turns advance only when the
current holder (or master) calls ``advance_pbp_turn`` — not on each message or roll.

Turn resolution priority:
1. If ``combat.initiative_order`` is non-empty → entity-based turns via
   ``combat.current_turn_entity_id`` (narrative or combat PBP).
2. Otherwise → user-based turns via ``turn_management.current_turn_player_id`` and
   ``turn_management.turn_order``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import CampaignEntity
from app.models.user import User
from app.schemas.scene import InitiativeEntry, SceneState, TurnOrderSource
from app.services.combat_resolver import CombatResolverError, entity_display_name, get_entity_sheet
from app.services.entities import find_pc_by_user


class PbpTurnError(ValueError):
    pass


def is_pbp_enforcement_active(state: SceneState) -> bool:
    return bool(state.turn_management.pbp_enabled)


def _read_entity_attribute_score(entity: CampaignEntity, attribute: str = "dexterity") -> int:
    try:
        sheet = get_entity_sheet(entity)
    except CombatResolverError:
        return 10
    abilities = sheet.get("abilities", {})
    if not isinstance(abilities, dict):
        return 10
    key = attribute.strip().lower()
    if key in {"dexterity", "dex"}:
        key = "dex"
    elif key in {"strength", "str"}:
        key = "str"
    elif key in {"constitution", "con"}:
        key = "con"
    elif key in {"intelligence", "int"}:
        key = "int"
    elif key in {"wisdom", "wis"}:
        key = "wis"
    elif key in {"charisma", "cha"}:
        key = "cha"
    score = abilities.get(key, 10)
    return int(score) if isinstance(score, (int, float)) else 10


def sort_initiative_entries(
    entries: list[InitiativeEntry],
    entities_by_id: dict[str, CampaignEntity],
    order_source: TurnOrderSource,
) -> list[InitiativeEntry]:
    if order_source == "manual" or not entries:
        return list(entries)

    if order_source == "initiative":
        return sorted(entries, key=lambda item: item.initiative_score or 0, reverse=True)

    return sorted(
        entries,
        key=lambda item: (
            _read_entity_attribute_score(entities_by_id[str(item.entity_id)], "dexterity")
            if str(item.entity_id) in entities_by_id
            else 0
        ),
        reverse=True,
    )


async def fetch_entities_by_id(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    entity_ids: list[str],
) -> dict[str, CampaignEntity]:
    parsed: list[uuid.UUID] = []
    for raw_id in entity_ids:
        try:
            parsed.append(uuid.UUID(str(raw_id)))
        except ValueError:
            continue
    if not parsed:
        return {}

    rows = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.id.in_(parsed),
            )
        )
    ).all()
    return {str(entity.id): entity for entity in rows}


def build_default_pbp_order(
    state: SceneState,
    entities: list[CampaignEntity],
) -> list[InitiativeEntry]:
    """Build narrative PBP order from entities present in scene (PCs + active NPCs)."""
    initiative_ids = {str(entry.entity_id) for entry in state.combat.initiative_order}
    active_npc_ids = set(state.context.active_npc_ids)

    pcs: list[CampaignEntity] = []
    npcs: list[CampaignEntity] = []
    for entity in entities:
        if entity.entity_type == "PC":
            flags = entity.document.get("state_flags", {})
            present = isinstance(flags, dict) and bool(flags.get("is_present_in_scene"))
            if present or str(entity.id) in initiative_ids:
                pcs.append(entity)
        elif entity.entity_type == "NPC":
            if str(entity.id) in active_npc_ids or str(entity.id) in initiative_ids:
                npcs.append(entity)

    ordered = sorted(pcs, key=entity_display_name) + sorted(npcs, key=entity_display_name)
    return [
        InitiativeEntry(
            entity_id=str(entity.id),
            entity_type=entity.entity_type,
            display_name=entity_display_name(entity),
            is_active=True,
        )
        for entity in ordered
    ]


async def ensure_pbp_initiative_order(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    state: SceneState,
) -> bool:
    """Populate ``combat.initiative_order`` from scene entities when empty."""
    if state.combat.initiative_order:
        return False

    from app.services.combat_resolver import fetch_scene_combat_entities

    entities = await fetch_scene_combat_entities(db, campaign_id, state)
    entries = build_default_pbp_order(state, entities)
    if not entries:
        return False

    state.combat.initiative_order = entries
    if not state.combat.current_turn_entity_id:
        state.combat.current_turn_entity_id = entries[0].entity_id
    await sync_turn_management_from_initiative(db, campaign_id, state)
    return True


async def sync_turn_management_from_initiative(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    state: SceneState,
) -> None:
    """Align narrative turn_order / current_turn_player_id with initiative_order."""
    user_ids: list[str] = []
    for entry in state.combat.initiative_order:
        entity = await db.scalar(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.id == uuid.UUID(str(entry.entity_id)),
            )
        )
        if entity is None or entity.entity_type != "PC":
            continue
        binding = entity.document.get("player_binding", {})
        if isinstance(binding, dict) and binding.get("user_id"):
            uid = str(binding["user_id"])
            if uid not in user_ids:
                user_ids.append(uid)

    if user_ids:
        state.turn_management.turn_order = user_ids

    current_entity_id = state.combat.current_turn_entity_id
    if not current_entity_id and state.combat.initiative_order:
        current_entity_id = state.combat.initiative_order[0].entity_id
        state.combat.current_turn_entity_id = current_entity_id

    state.turn_management.current_turn_player_id = None
    if current_entity_id:
        entity = await db.scalar(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.id == uuid.UUID(str(current_entity_id)),
            )
        )
        if entity is not None and entity.entity_type == "PC":
            binding = entity.document.get("player_binding", {})
            if isinstance(binding, dict) and binding.get("user_id"):
                state.turn_management.current_turn_player_id = str(binding["user_id"])


def _format_turn_holder_label(character_name: str, player_display_name: str | None = None) -> str:
    if player_display_name and player_display_name.strip():
        return f"{character_name} ({player_display_name.strip()})"
    return character_name


async def _resolve_user_display_name(db: AsyncSession, user_id: str | uuid.UUID) -> str | None:
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        return None
    user = await db.scalar(select(User).where(User.id == user_uuid))
    return user.display_name if user is not None else None


async def resolve_current_turn_display_name(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    state: SceneState,
) -> str | None:
    if state.combat.initiative_order:
        current_entity_id = state.combat.current_turn_entity_id
        if not current_entity_id:
            current_entity_id = state.combat.initiative_order[0].entity_id
        if current_entity_id:
            entity = await db.scalar(
                select(CampaignEntity).where(
                    CampaignEntity.campaign_id == campaign_id,
                    CampaignEntity.id == uuid.UUID(str(current_entity_id)),
                )
            )
            if entity is not None:
                character_name = entity_display_name(entity)
                if entity.entity_type == "PC":
                    binding = entity.document.get("player_binding", {})
                    user_id = binding.get("user_id") if isinstance(binding, dict) else None
                    player_name = await _resolve_user_display_name(db, str(user_id)) if user_id else None
                    return _format_turn_holder_label(character_name, player_name)
                return character_name
        for entry in state.combat.initiative_order:
            if str(entry.entity_id) == str(current_entity_id):
                if entry.display_name:
                    return entry.display_name
                break
        return None

    current_player_id = state.turn_management.current_turn_player_id
    if not current_player_id:
        return None
    player_name = await _resolve_user_display_name(db, current_player_id)
    try:
        user_uuid = uuid.UUID(str(current_player_id))
    except ValueError:
        return player_name or str(current_player_id)
    pc = await find_pc_by_user(db, campaign_id, user_uuid)
    if pc is not None:
        return _format_turn_holder_label(entity_display_name(pc), player_name)
    return player_name or str(current_player_id)


async def assert_pbp_advance_allowed(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    state: SceneState,
    user_id: str,
    user_role: str,
) -> None:
    """Only the current turn holder or master may end the turn manually."""
    if user_role == "MASTER":
        return
    if not is_pbp_enforcement_active(state):
        raise PbpTurnError("PBP mode is not enabled")

    if state.combat.initiative_order:
        current_entity_id = state.combat.current_turn_entity_id
        if not current_entity_id:
            current_entity_id = state.combat.initiative_order[0].entity_id

        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError as exc:
            raise PbpTurnError("Invalid user") from exc

        pc = await find_pc_by_user(db, campaign_id, user_uuid)
        if pc is None:
            raise PbpTurnError("No tienes un personaje en esta campaña")

        if str(pc.id) != str(current_entity_id):
            holder = await resolve_current_turn_display_name(db, campaign_id, state)
            label = holder or "otro jugador"
            raise PbpTurnError(f"Solo quien tiene el turno puede avanzarlo. Turno de {label}.")
        return

    current_player_id = state.turn_management.current_turn_player_id
    if current_player_id and str(user_id) != str(current_player_id):
        holder = await resolve_current_turn_display_name(db, campaign_id, state)
        label = holder or "otro jugador"
        raise PbpTurnError(f"Solo quien tiene el turno puede avanzarlo. Turno de {label}.")


async def assert_pbp_post_allowed(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    state: SceneState,
    sender_id: str,
    sender_role: str,
) -> None:
    if sender_role == "MASTER":
        return
    if not is_pbp_enforcement_active(state):
        return

    if state.combat.initiative_order:
        current_entity_id = state.combat.current_turn_entity_id
        if not current_entity_id:
            current_entity_id = state.combat.initiative_order[0].entity_id

        try:
            user_uuid = uuid.UUID(str(sender_id))
        except ValueError as exc:
            raise PbpTurnError("Invalid sender") from exc

        pc = await find_pc_by_user(db, campaign_id, user_uuid)
        if pc is None:
            raise PbpTurnError("No tienes un personaje en esta campaña")

        if str(pc.id) != str(current_entity_id):
            holder = await resolve_current_turn_display_name(db, campaign_id, state)
            label = holder or "otro jugador"
            raise PbpTurnError(f"No es tu turno. Turno de {label}.")
        return

    current_player_id = state.turn_management.current_turn_player_id
    if current_player_id and str(sender_id) != str(current_player_id):
        holder = await resolve_current_turn_display_name(db, campaign_id, state)
        label = holder or "otro jugador"
        raise PbpTurnError(f"No es tu turno. Turno de {label}.")


def advance_pbp_turn(state: SceneState) -> None:
    """Advance to the next holder when the current player ends their turn."""
    if not is_pbp_enforcement_active(state):
        return

    if state.combat.initiative_order:
        order = state.combat.initiative_order
        current_id = state.combat.current_turn_entity_id or order[0].entity_id
        current_index = next(
            (index for index, entry in enumerate(order) if str(entry.entity_id) == str(current_id)),
            0,
        )
        next_index = (current_index + 1) % len(order)
        state.combat.current_turn_entity_id = order[next_index].entity_id
        return

    turn_order = state.turn_management.turn_order
    if not turn_order:
        return

    current_player_id = state.turn_management.current_turn_player_id
    if current_player_id not in turn_order:
        state.turn_management.current_turn_player_id = turn_order[0]
        return

    current_index = turn_order.index(str(current_player_id))
    next_index = (current_index + 1) % len(turn_order)
    state.turn_management.current_turn_player_id = turn_order[next_index]

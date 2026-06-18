import uuid
import unicodedata
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignEntity
from app.rules.base import AttackContext, DamageResult, GameSystemPlugin, RollContext
from app.rules.registry import get_plugin
from app.schemas.scene import InitiativeEntry, SceneState
from app.services.combat_parser import (
    ParsedAttackCommand,
    ParsedCombatCommand,
    ParsedDamageCommand,
    ParsedInitiativeCommand,
    normalize_mention,
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class CombatResolverError(ValueError):
    pass


@dataclass
class CombatExecutionResult:
    messages: list[dict[str, Any]]
    state: SceneState


_COMBAT_SUPPORTED_SYSTEMS = frozenset({"dnd5e", "cyberpunk_red"})


def get_combat_plugin(game_system: str | None) -> GameSystemPlugin:
    plugin = get_plugin(game_system)
    if plugin.system_id not in _COMBAT_SUPPORTED_SYSTEMS:
        label = game_system or "generic"
        supported = ", ".join(sorted(_COMBAT_SUPPORTED_SYSTEMS))
        raise CombatResolverError(
            f"Automated combat is not supported for game system {label!r}. "
            f"Currently supported: {supported}."
        )
    return plugin


def entity_display_name(entity: CampaignEntity) -> str:
    identity = entity.document.get("identity", {})
    if isinstance(identity, dict):
        name = identity.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return str(entity.id)


def get_entity_sheet(entity: CampaignEntity) -> dict[str, Any]:
    system_mechanics = entity.document.get("system_mechanics", {})
    if not isinstance(system_mechanics, dict):
        raise CombatResolverError(f"{entity_display_name(entity)} has no combat sheet")
    sheet = system_mechanics.get("sheet")
    if not isinstance(sheet, dict) or not sheet:
        raise CombatResolverError(f"{entity_display_name(entity)} has no combat sheet")
    return sheet


def normalize_entity_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.lower().strip()


def resolve_entity_reference(
    ref: str,
    entities: list[CampaignEntity],
) -> CampaignEntity:
    normalized_ref = normalize_entity_name(normalize_mention(ref))
    if not normalized_ref:
        raise CombatResolverError("Entity reference is empty")

    by_id = [entity for entity in entities if str(entity.id).lower() == normalized_ref]
    if len(by_id) == 1:
        return by_id[0]

    exact_name_matches: list[CampaignEntity] = []
    partial_name_matches: list[CampaignEntity] = []
    for entity in entities:
        name = normalize_entity_name(entity_display_name(entity))
        if name == normalized_ref:
            exact_name_matches.append(entity)
        elif normalized_ref in name or name in normalized_ref:
            partial_name_matches.append(entity)

    if len(exact_name_matches) == 1:
        return exact_name_matches[0]
    if len(exact_name_matches) > 1:
        names = ", ".join(entity_display_name(entity) for entity in exact_name_matches)
        raise CombatResolverError(f"Ambiguous entity name {ref!r}: matches {names}")

    if len(partial_name_matches) == 1:
        return partial_name_matches[0]
    if len(partial_name_matches) > 1:
        names = ", ".join(entity_display_name(entity) for entity in partial_name_matches)
        raise CombatResolverError(f"Ambiguous entity name {ref!r}: matches {names}")

    raise CombatResolverError(f"No entity in scene matches {ref!r}")


def assert_attacker_permission(
    attacker: CampaignEntity,
    *,
    sender_id: str,
    sender_role: str,
) -> None:
    if sender_role == "MASTER":
        return
    if attacker.entity_type != "PC":
        raise CombatResolverError("Players can only attack with their own character")
    binding = attacker.document.get("player_binding", {})
    if not isinstance(binding, dict) or binding.get("user_id") != sender_id:
        raise CombatResolverError("You can only attack with your own character")


def assert_master_only(sender_role: str, action: str) -> None:
    if sender_role != "MASTER":
        raise CombatResolverError(f"Only the Master can use {action}")


def _set_initiative_order(state: SceneState, entries: list[InitiativeEntry]) -> None:
    state.combat.initiative_order = entries
    if entries and state.combat.current_turn_entity_id is None:
        state.combat.current_turn_entity_id = entries[0].entity_id


def _set_combat_active(state: SceneState, active: bool) -> None:
    state.combat.is_active = active
    state.combat.conflict_mode_active = active
    state.state_flags.conflict_mode_active = active
    if not active:
        state.combat.current_turn_entity_id = None


def _set_combat_round(state: SceneState, round_number: int) -> None:
    state.combat.round = max(0, round_number)


async def fetch_scene_combat_entities(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    state: SceneState,
) -> list[CampaignEntity]:
    entities: list[CampaignEntity] = []
    seen_ids: set[uuid.UUID] = set()

    initiative_ids: set[uuid.UUID] = set()
    for entry in state.combat.initiative_order:
        try:
            initiative_ids.add(uuid.UUID(str(entry.entity_id)))
        except ValueError:
            continue

    pcs = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.entity_type == "PC",
            )
        )
    ).all()
    for pc in pcs:
        flags = pc.document.get("state_flags", {})
        present = isinstance(flags, dict) and bool(flags.get("is_present_in_scene"))
        in_initiative = pc.id in initiative_ids
        if present or in_initiative or not initiative_ids:
            entities.append(pc)
            seen_ids.add(pc.id)

    npc_ids: list[uuid.UUID] = []
    seen_npc_ids: set[uuid.UUID] = set()
    for raw_id in state.context.active_npc_ids:
        try:
            parsed = uuid.UUID(str(raw_id))
        except ValueError:
            continue
        if parsed not in seen_npc_ids:
            npc_ids.append(parsed)
            seen_npc_ids.add(parsed)
    for entry in state.combat.initiative_order:
        try:
            parsed = uuid.UUID(str(entry.entity_id))
        except ValueError:
            continue
        if parsed not in seen_npc_ids:
            npc_ids.append(parsed)
            seen_npc_ids.add(parsed)

    if npc_ids:
        npcs = (
            await db.scalars(
                select(CampaignEntity).where(
                    CampaignEntity.campaign_id == campaign_id,
                    CampaignEntity.id.in_(npc_ids),
                )
            )
        ).all()
        for npc in npcs:
            if npc.id not in seen_ids:
                entities.append(npc)
                seen_ids.add(npc.id)

    return entities


def _format_d20_attack_roll_line(attack_roll: Any, *, hit: bool | None) -> str:
    modifier = attack_roll.details.get("modifier", 0)
    if not isinstance(modifier, int):
        modifier = 0

    mod_str = ""
    if modifier > 0:
        mod_str = f" + {modifier}"
    elif modifier < 0:
        mod_str = f" - {abs(modifier)}"

    if attack_roll.details.get("advantage"):
        dice_label = "2d20 (ventaja)"
    elif attack_roll.details.get("disadvantage"):
        dice_label = "2d20 (desventaja)"
    else:
        dice_label = "1d20"

    line = f"{dice_label}{mod_str} = {attack_roll.total}"
    target_ac = attack_roll.details.get("target_ac")
    if target_ac is not None:
        line += f" vs CA {target_ac}"
    if hit is not None:
        line += f" — {'Impacto' if hit else 'Fallo'}"
    return line


def _build_attack_roll_payload(attack_roll: Any, *, hit: bool) -> dict[str, Any]:
    natural = attack_roll.rolls[-1] if attack_roll.rolls else None
    modifier = attack_roll.details.get("modifier")
    payload: dict[str, Any] = {
        "total": attack_roll.total,
        "hit": hit,
        "expression": attack_roll.expression,
        "rolls": attack_roll.rolls,
        "target_ac": attack_roll.details.get("target_ac"),
        "modifier": modifier if isinstance(modifier, int) else 0,
        "chat_summary": _format_d20_attack_roll_line(attack_roll, hit=hit),
    }
    if natural == 20:
        payload["natural_20"] = True
    if natural == 1:
        payload["natural_1"] = True
    return payload


def _persist_entity_sheet(
    entity: CampaignEntity,
    sheet: dict[str, Any],
    *,
    state_flag_updates: dict[str, bool] | None = None,
) -> None:
    document = deepcopy(entity.document)
    system_mechanics = document.get("system_mechanics", {})
    if not isinstance(system_mechanics, dict):
        system_mechanics = {}
    system_mechanics["sheet"] = sheet
    document["system_mechanics"] = system_mechanics

    if state_flag_updates:
        flags = document.get("state_flags", {})
        if not isinstance(flags, dict):
            flags = {}
        flags.update(state_flag_updates)
        document["state_flags"] = flags

    entity.document = document


def _build_attack_messages(
    *,
    sender_id: str,
    attacker: CampaignEntity,
    defender: CampaignEntity,
    attack_result: Any,
    damage_application: Any | None,
    weapon_name: str | None = None,
) -> list[dict[str, Any]]:
    attacker_name = entity_display_name(attacker)
    defender_name = entity_display_name(defender)
    attack_roll = attack_result.attack_roll
    roll_line = _format_d20_attack_roll_line(attack_roll, hit=attack_result.hit)
    resolved_weapon = weapon_name or attack_roll.details.get("attack_name")
    if isinstance(resolved_weapon, str) and not resolved_weapon.strip():
        resolved_weapon = None

    if attack_result.hit and attack_result.damage is not None:
        summary = (
            f"{attacker_name} ataca a {defender_name}: "
            f"{roll_line}. "
            f"{attack_result.damage.amount} {attack_result.damage.damage_type}."
        )
        if damage_application is not None:
            summary += f" PV {damage_application.hp_before} → {damage_application.hp_after}."
    else:
        summary = f"{attacker_name} ataca a {defender_name}: {roll_line}."

    combat_event: dict[str, Any] = {
        "kind": "ATTACK_RESOLVED",
        "attacker_id": str(attacker.id),
        "attacker_name": attacker_name,
        "defender_id": str(defender.id),
        "defender_name": defender_name,
        "attack_roll": _build_attack_roll_payload(attack_roll, hit=attack_result.hit),
    }
    if isinstance(resolved_weapon, str):
        combat_event["weapon_name"] = resolved_weapon
    if attack_result.damage is not None:
        combat_event["damage"] = {
            "amount": attack_result.damage.amount,
            "type": attack_result.damage.damage_type,
            "expression": attack_result.damage.expression,
            "rolls": attack_result.damage.rolls,
        }
    if damage_application is not None:
        combat_event["hp"] = {
            "before": damage_application.hp_before,
            "after": damage_application.hp_after,
        }
        combat_event["defender_hp_remaining"] = damage_application.hp_after

    return [
        {
            "id": str(uuid.uuid4()),
            "timestamp": _utc_now_iso(),
            "sender_id": sender_id,
            "type": "COMBAT",
            "text": summary,
            "chat_summary": roll_line,
            "entity_id": str(attacker.id),
            "entity_name": attacker_name,
            "combat_event": combat_event,
            "read_by": [sender_id],
        },
    ]


def _sync_initiative_hp_flags(state: SceneState, entity: CampaignEntity) -> None:
    flags = entity.document.get("state_flags", {})
    if not isinstance(flags, dict):
        return
    for entry in state.combat.initiative_order:
        if entry.entity_id == str(entity.id):
            entry.is_active = not bool(flags.get("is_dead") or flags.get("is_incapacitated"))


async def execute_attack(
    db: AsyncSession,
    campaign: Campaign,
    state: SceneState,
    *,
    sender_id: str,
    sender_role: str,
    attacker_ref: str,
    defender_ref: str,
    weapon_name: str | None = None,
    attack_index: int | None = None,
) -> CombatExecutionResult:
    plugin = get_combat_plugin(campaign.game_system)
    scene_entities = await fetch_scene_combat_entities(db, campaign.id, state)

    attacker = resolve_entity_reference(attacker_ref, scene_entities)
    defender = resolve_entity_reference(defender_ref, scene_entities)
    assert_attacker_permission(attacker, sender_id=sender_id, sender_role=sender_role)

    if attacker.id == defender.id:
        raise CombatResolverError("Attacker and defender must be different entities")

    attacker_sheet = get_entity_sheet(attacker)
    defender_sheet = get_entity_sheet(defender)

    attack_result = plugin.resolve_attack(
        attacker_sheet,
        defender_sheet,
        weapon_name,
        AttackContext(attack_name=weapon_name, attack_index=attack_index),
    )

    damage_application = None
    if attack_result.hit and attack_result.damage is not None:
        updated_sheet, damage_application = plugin.apply_damage(defender_sheet, attack_result.damage)
        flag_updates: dict[str, bool] = {}
        if damage_application.is_unconscious:
            if defender.entity_type == "PC":
                flag_updates["is_incapacitated"] = True
            elif defender.entity_type == "NPC":
                flag_updates["is_dead"] = True
        _persist_entity_sheet(defender, updated_sheet, state_flag_updates=flag_updates or None)
        _sync_initiative_hp_flags(state, defender)

    messages = _build_attack_messages(
        sender_id=sender_id,
        attacker=attacker,
        defender=defender,
        attack_result=attack_result,
        damage_application=damage_application,
        weapon_name=weapon_name,
    )
    return CombatExecutionResult(messages=messages, state=state)


async def execute_manual_damage(
    db: AsyncSession,
    campaign: Campaign,
    state: SceneState,
    *,
    sender_id: str,
    sender_role: str,
    target_ref: str,
    amount: int,
    damage_type: str,
) -> CombatExecutionResult:
    assert_master_only(sender_role, "/damage")
    plugin = get_combat_plugin(campaign.game_system)
    scene_entities = await fetch_scene_combat_entities(db, campaign.id, state)
    target = resolve_entity_reference(target_ref, scene_entities)
    defender_sheet = get_entity_sheet(target)

    damage = DamageResult(
        amount=amount,
        expression=str(amount),
        rolls=[],
        damage_type=damage_type,
    )
    updated_sheet, damage_application = plugin.apply_damage(defender_sheet, damage)
    flag_updates: dict[str, bool] = {}
    if damage_application.is_unconscious:
        if target.entity_type == "PC":
            flag_updates["is_incapacitated"] = True
        elif target.entity_type == "NPC":
            flag_updates["is_dead"] = True
    _persist_entity_sheet(target, updated_sheet, state_flag_updates=flag_updates or None)
    _sync_initiative_hp_flags(state, target)

    target_name = entity_display_name(target)
    summary = (
        f"Daño manual a {target_name}: {amount} {damage_type}. "
        f"PV {damage_application.hp_before} → {damage_application.hp_after}."
    )
    messages = [
        {
            "id": str(uuid.uuid4()),
            "timestamp": _utc_now_iso(),
            "sender_id": sender_id,
            "type": "COMBAT",
            "text": summary,
            "combat_event": {
                "kind": "DAMAGE_APPLIED",
                "defender_id": str(target.id),
                "defender_name": target_name,
                "damage": {"amount": amount, "type": damage_type},
                "hp": {
                    "before": damage_application.hp_before,
                    "after": damage_application.hp_after,
                },
                "defender_hp_remaining": damage_application.hp_after,
            },
            "entity_id": str(target.id),
            "entity_name": target_name,
            "read_by": [sender_id],
        }
    ]
    return CombatExecutionResult(messages=messages, state=state)


async def execute_initiative(
    db: AsyncSession,
    campaign: Campaign,
    state: SceneState,
    *,
    sender_id: str,
    sender_role: str,
    activate_combat: bool = True,
) -> CombatExecutionResult:
    assert_master_only(sender_role, "initiative rolls")
    plugin = get_combat_plugin(campaign.game_system)
    scene_entities = await fetch_scene_combat_entities(db, campaign.id, state)
    if not scene_entities:
        raise CombatResolverError("No entities present in scene for initiative")

    entries: list[InitiativeEntry] = []
    roll_messages: list[dict[str, Any]] = []
    for entity in scene_entities:
        sheet = get_entity_sheet(entity)
        roll = plugin.resolve_roll("initiative", sheet, RollContext())
        entries.append(
            InitiativeEntry(
                entity_id=str(entity.id),
                entity_type=entity.entity_type,
                display_name=entity_display_name(entity),
                initiative_score=roll.total,
                is_active=True,
            )
        )
        roll_messages.append(
            {
                "id": str(uuid.uuid4()),
                "timestamp": _utc_now_iso(),
                "sender_id": sender_id,
                "type": "DICE_ROLL",
                "text": f"{entity_display_name(entity)} — {roll.chat_summary}",
                "entity_id": str(entity.id),
                "roll_type": "initiative",
                "roll_details": {
                    "total": roll.total,
                    "rolls": roll.rolls,
                    "expression": roll.expression,
                },
                "final_result": roll.total,
                "read_by": [sender_id],
            }
        )

    entries.sort(key=lambda item: item.initiative_score or 0, reverse=True)
    _set_initiative_order(state, entries)
    if activate_combat:
        _set_combat_active(state, True)
        _set_combat_round(state, 1)
    elif entries:
        state.combat.current_turn_entity_id = entries[0].entity_id

    from app.services.pbp_turn import sync_turn_management_from_initiative

    await sync_turn_management_from_initiative(db, campaign.id, state)

    summary = "Iniciativa: " + ", ".join(
        f"{entry.display_name} ({entry.initiative_score})" for entry in entries
    )
    combat_message = {
        "id": str(uuid.uuid4()),
        "timestamp": _utc_now_iso(),
        "sender_id": sender_id,
        "type": "COMBAT",
        "text": summary,
        "combat_event": {
            "kind": "INITIATIVE_ROLLED",
            "initiative_order": [entry.model_dump() for entry in entries],
        },
        "read_by": [sender_id],
    }
    return CombatExecutionResult(messages=[combat_message, *roll_messages], state=state)


async def execute_combat_command(
    db: AsyncSession,
    campaign: Campaign,
    state: SceneState,
    *,
    sender_id: str,
    sender_role: str,
    command: ParsedCombatCommand,
) -> CombatExecutionResult:
    if isinstance(command, ParsedAttackCommand):
        result = await execute_attack(
            db,
            campaign,
            state,
            sender_id=sender_id,
            sender_role=sender_role,
            attacker_ref=command.attacker_ref,
            defender_ref=command.defender_ref,
            weapon_name=command.weapon_name,
        )
    elif isinstance(command, ParsedDamageCommand):
        result = await execute_manual_damage(
            db,
            campaign,
            state,
            sender_id=sender_id,
            sender_role=sender_role,
            target_ref=command.target_ref,
            amount=command.amount,
            damage_type=command.damage_type,
        )
    elif isinstance(command, ParsedInitiativeCommand):
        result = await execute_initiative(
            db,
            campaign,
            state,
            sender_id=sender_id,
            sender_role=sender_role,
        )
    else:
        raise CombatResolverError(f"Unsupported combat command: {command}")

    return result

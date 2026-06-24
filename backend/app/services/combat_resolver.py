import re
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


def _normalize_mention(ref: str) -> str:
    return ref.lstrip("@").strip()


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
    normalized_ref = normalize_entity_name(_normalize_mention(ref))
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
    if attack_roll.details.get("resolution") == "save" and isinstance(getattr(attack_roll, "chat_summary", None), str):
        return str(attack_roll.chat_summary)

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
    save_dc = attack_roll.details.get("save_dc") or attack_roll.details.get("dc")
    target_ac = attack_roll.details.get("target_ac")
    if save_dc is not None:
        line += f" vs CD {save_dc}"
        save_succeeded = attack_roll.details.get("save_succeeded")
        if save_succeeded is None and attack_roll.success is not None:
            save_succeeded = attack_roll.success
        if save_succeeded is not None:
            line += f" — {'éxito' if save_succeeded else 'fallo'}"
    elif target_ac is not None:
        line += f" vs CA {target_ac}"
        if hit is not None:
            line += f" — {'Impacto' if hit else 'Fallo'}"
    return line


def _format_damage_line(damage: Any, *, is_healing: bool = False) -> str:
    expression = getattr(damage, "expression", None)
    rolls = getattr(damage, "rolls", None)
    amount = getattr(damage, "amount", 0)
    modifier = getattr(damage, "modifier", 0)
    damage_type = getattr(damage, "damage_type", None)
    if hasattr(damage, "is_healing"):
        is_healing = bool(getattr(damage, "is_healing", False)) or is_healing
    elif isinstance(damage, dict):
        is_healing = bool(damage.get("is_healing")) or is_healing

    dice_sides = None
    if isinstance(expression, str):
        match = re.match(r"(\d+)d(\d+)", expression)
        if match:
            dice_sides = int(match.group(2))

    if isinstance(rolls, list) and rolls:
        die = f"d{dice_sides}" if dice_sides else "d?"
        dice_part = f"1{die}={rolls[0]}" if len(rolls) == 1 else f"[{', '.join(str(r) for r in rolls)}]"
    else:
        dice_part = expression or "?"

    line = dice_part
    if isinstance(modifier, int) and modifier:
        line += f" {modifier:+d}"
    line += f" = {amount}"
    if isinstance(damage_type, str) and damage_type.strip():
        line += f" {damage_type.replace('_', ' ')}"
    if is_healing:
        return f"Curación {line}"
    return line


def _build_attack_roll_payload(attack_roll: Any, *, hit: bool) -> dict[str, Any]:
    natural = attack_roll.rolls[-1] if attack_roll.rolls else None
    modifier = attack_roll.details.get("modifier")
    is_critical = bool(attack_roll.details.get("is_critical")) or natural == 20
    save_dc = attack_roll.details.get("save_dc") or attack_roll.details.get("dc")
    payload: dict[str, Any] = {
        "total": attack_roll.total,
        "hit": hit,
        "expression": attack_roll.expression,
        "rolls": attack_roll.rolls,
        "target_ac": attack_roll.details.get("target_ac"),
        "modifier": modifier if isinstance(modifier, int) else 0,
        "chat_summary": _format_d20_attack_roll_line(attack_roll, hit=hit),
    }
    if save_dc is not None:
        payload["save_dc"] = save_dc
        save_succeeded = attack_roll.details.get("save_succeeded")
        if save_succeeded is None and attack_roll.success is not None:
            save_succeeded = attack_roll.success
        if save_succeeded is not None:
            payload["save_succeeded"] = save_succeeded
        save_ability = attack_roll.details.get("save_ability") or attack_roll.details.get("ability")
        if isinstance(save_ability, str) and save_ability.strip():
            payload["save_ability"] = save_ability
        payload["resolution"] = "save"
    if natural == 20:
        payload["natural_20"] = True
    if natural == 1:
        payload["natural_1"] = True
    if is_critical:
        payload["is_critical"] = True
    return payload


def _damage_flag_updates(entity: CampaignEntity, damage_application: Any) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    if damage_application.is_healing:
        if damage_application.hp_after > 0 and entity.entity_type == "PC":
            flags["is_incapacitated"] = False
            flags["is_dead"] = False
        return flags

    if damage_application.is_instant_death or damage_application.is_dead:
        flags["is_incapacitated"] = True
        if entity.entity_type == "NPC" or damage_application.is_instant_death or damage_application.is_dead:
            flags["is_dead"] = True
        return flags

    if damage_application.is_unconscious:
        flags["is_incapacitated"] = True
        if entity.entity_type == "NPC":
            flags["is_dead"] = True
    return flags


def _format_damage_application_line(damage_application: Any, damage: Any, *, is_healing: bool = False) -> str:
    if is_healing:
        return _format_damage_line(damage, is_healing=True)

    raw_amount = getattr(damage_application, "raw_amount", None)
    modified_amount = getattr(damage_application, "modified_amount", None)
    modifier_label = getattr(damage_application, "damage_modifier", None)
    damage_type = getattr(damage, "damage_type", None) or getattr(damage_application, "damage_type", "")

    if (
        isinstance(raw_amount, int)
        and isinstance(modified_amount, int)
        and modifier_label
        and raw_amount != modified_amount
    ):
        type_label = str(damage_type).replace("_", " ")
        line = f"{raw_amount} {type_label} → {modified_amount} ({modifier_label})"
    else:
        line = _format_damage_line(damage, is_healing=False)

    if getattr(damage, "is_critical", False) or getattr(damage_application, "is_critical", False):
        line = f"{line} — crítico"
    return line


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
    hidden_npc_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    hidden_npc_ids = hidden_npc_ids or set()
    attacker_name = entity_display_name(attacker)
    defender_name = entity_display_name(defender)
    attack_roll = attack_result.attack_roll
    is_save_attack = attack_roll.details.get("resolution") == "save"
    roll_line = _format_d20_attack_roll_line(attack_roll, hit=attack_result.hit)
    resolved_weapon = weapon_name or attack_roll.details.get("attack_name")
    if isinstance(resolved_weapon, str) and not resolved_weapon.strip():
        resolved_weapon = None

    if attack_result.hit and attack_result.damage is not None:
        is_healing = bool(getattr(attack_result.damage, "is_healing", False))
        effect_line = _format_damage_application_line(
            damage_application,
            attack_result.damage,
            is_healing=is_healing,
        )
        verb = "cura a" if is_healing else ("lanza contra" if is_save_attack else "ataca a")
        summary = (
            f"{attacker_name} {verb} {defender_name}: "
        )
        if not is_healing:
            summary += f"{roll_line}. "
        summary += f"{effect_line}."
        if damage_application is not None:
            summary += f" PV {damage_application.hp_before} → {damage_application.hp_after}."
            if damage_application.is_instant_death:
                summary += " Muerte instantánea."
            elif damage_application.death_save_failures_added:
                summary += f" +{damage_application.death_save_failures_added} fallo(s) de salvación."
    elif is_save_attack:
        verb = "lanza contra"
        summary = f"{attacker_name} {verb} {defender_name}: {roll_line}."
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
        damage = attack_result.damage
        is_healing = bool(getattr(damage, "is_healing", False))
        combat_event["damage"] = {
            "amount": damage.amount,
            "type": damage.damage_type,
            "expression": damage.expression,
            "rolls": damage.rolls,
            "modifier": damage.modifier,
            "is_healing": is_healing,
            "is_critical": bool(getattr(damage, "is_critical", False)),
            "chat_summary": _format_damage_application_line(
                damage_application,
                damage,
                is_healing=is_healing,
            )
            if damage_application is not None
            else _format_damage_line(damage, is_healing=is_healing),
        }
        if damage_application is not None:
            if damage_application.raw_amount is not None:
                combat_event["damage"]["raw_amount"] = damage_application.raw_amount
            if damage_application.modified_amount is not None:
                combat_event["damage"]["modified_amount"] = damage_application.modified_amount
            if damage_application.damage_modifier:
                combat_event["damage"]["damage_modifier"] = damage_application.damage_modifier
        if is_healing:
            combat_event["is_healing"] = True
    if damage_application is not None:
        combat_event["hp"] = {
            "before": damage_application.hp_before,
            "after": damage_application.hp_after,
        }
        combat_event["defender_hp_remaining"] = damage_application.hp_after
        if damage_application.is_instant_death:
            combat_event["is_instant_death"] = True
        if damage_application.is_critical:
            combat_event["is_critical"] = True
        if damage_application.death_save_failures_added:
            combat_event["death_save_failures_added"] = damage_application.death_save_failures_added

    visibility = "master_only" if str(attacker.id) in hidden_npc_ids else "all"

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
            "visibility": visibility,
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
    advantage: bool = False,
    disadvantage: bool = False,
) -> CombatExecutionResult:
    plugin = get_combat_plugin(campaign.game_system)
    scene_entities = await fetch_scene_combat_entities(db, campaign.id, state)

    from app.services.entities import get_effective_hidden_npc_ids

    hidden_npc_ids = await get_effective_hidden_npc_ids(db, campaign.id)

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
        AttackContext(
            attack_name=weapon_name,
            attack_index=attack_index,
            advantage=advantage,
            disadvantage=disadvantage,
        ),
    )

    damage_application = None
    if attack_result.hit and attack_result.damage is not None:
        updated_sheet, damage_application = plugin.apply_damage(defender_sheet, attack_result.damage)
        flag_updates = _damage_flag_updates(defender, damage_application)
        _persist_entity_sheet(defender, updated_sheet, state_flag_updates=flag_updates or None)
        _sync_initiative_hp_flags(state, defender)

    messages = _build_attack_messages(
        sender_id=sender_id,
        attacker=attacker,
        defender=defender,
        attack_result=attack_result,
        damage_application=damage_application,
        weapon_name=weapon_name,
        hidden_npc_ids=hidden_npc_ids,
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
    flag_updates = _damage_flag_updates(target, damage_application)
    _persist_entity_sheet(target, updated_sheet, state_flag_updates=flag_updates or None)
    _sync_initiative_hp_flags(state, target)

    target_name = entity_display_name(target)
    effect_line = _format_damage_application_line(damage_application, damage)
    summary = (
        f"Daño manual a {target_name}: {effect_line}. "
        f"PV {damage_application.hp_before} → {damage_application.hp_after}."
    )
    if damage_application.is_instant_death:
        summary += " Muerte instantánea."
    elif damage_application.death_save_failures_added:
        summary += f" +{damage_application.death_save_failures_added} fallo(s) de salvación."
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
                "damage": {
                    "amount": damage_application.modified_amount
                    if damage_application.modified_amount is not None
                    else amount,
                    "raw_amount": damage_application.raw_amount,
                    "modified_amount": damage_application.modified_amount,
                    "damage_modifier": damage_application.damage_modifier,
                    "type": damage_type,
                    "chat_summary": effect_line,
                },
                "hp": {
                    "before": damage_application.hp_before,
                    "after": damage_application.hp_after,
                },
                "defender_hp_remaining": damage_application.hp_after,
                "is_instant_death": damage_application.is_instant_death,
                "death_save_failures_added": damage_application.death_save_failures_added,
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
    entity_ids: list[str] | None = None,
) -> CombatExecutionResult:
    assert_master_only(sender_role, "initiative rolls")
    plugin = get_combat_plugin(campaign.game_system)
    if entity_ids:
        from app.services.pbp_turn import fetch_entities_by_id

        entities_by_id = await fetch_entities_by_id(db, campaign.id, entity_ids)
        scene_entities = [
            entities_by_id[str(entity_id)]
            for entity_id in entity_ids
            if str(entity_id) in entities_by_id
        ]
        if not scene_entities:
            raise CombatResolverError("No entities on initiative track")
    else:
        scene_entities = await fetch_scene_combat_entities(db, campaign.id, state)
        if not scene_entities:
            raise CombatResolverError("No entities present in scene for initiative")

    from app.services.entities import get_effective_hidden_npc_ids

    hidden_npc_ids = await get_effective_hidden_npc_ids(db, campaign.id)

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
                "visibility": "master_only" if str(entity.id) in hidden_npc_ids else "all",
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
        "visibility": "master_only" if hidden_npc_ids.intersection({entry.entity_id for entry in entries}) else "all",
    }
    return CombatExecutionResult(messages=[combat_message, *roll_messages], state=state)

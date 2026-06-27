import uuid
from copy import deepcopy
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignEntity
from app.rules.registry import get_plugin
from app.schemas.entities import (
    ENTITY_DOCUMENT_MODELS,
    CharacterSheetUpsert,
    EntityType,
    PCStateFlags,
    TypedSystemMechanics,
)
from app.services.dice import roll_dice


class EntityValidationError(ValueError):
    pass


class EntityReferenceError(ValueError):
    pass


def _is_nonempty_ref(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


async def validate_entity_cross_references(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    entity_type: EntityType,
    document: dict,
    entity_id: uuid.UUID | None = None,
) -> None:
    """Ensure referenced entity IDs exist in the same campaign."""
    refs: list[tuple[str, str, EntityType | None]] = []

    identity = document.get("identity")
    if isinstance(identity, dict):
        if _is_nonempty_ref(identity.get("faction_id")):
            refs.append(("identity.faction_id", identity["faction_id"], EntityType.FACTION))
        if _is_nonempty_ref(identity.get("current_location_id")):
            refs.append(("identity.current_location_id", identity["current_location_id"], EntityType.LOCATION))
        if _is_nonempty_ref(identity.get("headquarters_location_id")):
            refs.append(
                ("identity.headquarters_location_id", identity["headquarters_location_id"], EntityType.LOCATION),
            )
        if _is_nonempty_ref(identity.get("parent_location_id")):
            refs.append(("identity.parent_location_id", identity["parent_location_id"], EntityType.LOCATION))

    connection = document.get("connection")
    if isinstance(connection, dict):
        if _is_nonempty_ref(connection.get("source_id")):
            refs.append(("connection.source_id", connection["source_id"], None))
        if _is_nonempty_ref(connection.get("target_id")):
            refs.append(("connection.target_id", connection["target_id"], None))
        if entity_id is not None:
            entity_id_str = str(entity_id)
            for field, ref_id, _ in refs:
                if field.startswith("connection.") and ref_id == entity_id_str:
                    raise EntityReferenceError(f"{field}: an entity cannot reference itself")

    if not refs:
        return

    ref_ids = {uuid.UUID(ref_id) for _, ref_id, _ in refs}
    found = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.id.in_(ref_ids),
            )
        )
    ).all()
    found_by_id = {entity.id: entity for entity in found}

    for field, ref_id, expected_type in refs:
        try:
            ref_uuid = uuid.UUID(ref_id)
        except ValueError as exc:
            raise EntityReferenceError(f"{field}: invalid UUID {ref_id!r}") from exc

        target = found_by_id.get(ref_uuid)
        if target is None:
            raise EntityReferenceError(f"{field}: no entity with id {ref_id} in this campaign")
        if expected_type is not None and target.entity_type != expected_type.value:
            raise EntityReferenceError(
                f"{field}: entity {ref_id} is {target.entity_type}, expected {expected_type.value}",
            )


async def ensure_single_arc_manifest(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    entity_type: EntityType,
) -> None:
    if entity_type != EntityType.ARC_MANIFEST:
        return

    existing = await db.scalar(
        select(CampaignEntity.id).where(
            CampaignEntity.campaign_id == campaign_id,
            CampaignEntity.entity_type == EntityType.ARC_MANIFEST.value,
        )
    )
    if existing is not None:
        raise EntityReferenceError("Only one ARC_MANIFEST entity is allowed per campaign")


class CharacterSheetError(ValueError):
    pass


def _format_validation_error(exc: ValidationError, *, prefix: str = "") -> str:
    parts: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        field = f"{prefix}{loc}" if loc else prefix.rstrip(".")
        msg = err["msg"]
        parts.append(f"{field}: {msg}" if field else msg)
    return "; ".join(parts) if parts else str(exc)


def _is_typed_system_mechanics(mechanics: object) -> bool:
    return isinstance(mechanics, dict) and "system_id" in mechanics


def sync_combat_state_flags_from_hp(document: dict) -> dict:
    """Clear KO/death flags when sheet HP is above zero."""
    updated = deepcopy(document)
    mechanics = updated.get("system_mechanics")
    if not isinstance(mechanics, dict):
        return updated
    sheet = mechanics.get("sheet")
    if not isinstance(sheet, dict):
        return updated

    from app.rules.dnd5e.mechanics import read_hp_block

    hp_current = read_hp_block(sheet)["current"]
    if hp_current <= 0:
        return updated

    flags = updated.get("state_flags")
    if not isinstance(flags, dict):
        flags = {}
    flags["is_incapacitated"] = False
    if "is_dead" in flags:
        flags["is_dead"] = False
    updated["state_flags"] = flags
    return updated


def normalize_entity_document_for_campaign(
    *,
    campaign_game_system: str | None,
    entity_type: EntityType,
    document: dict,
) -> dict:
    """Validate typed sheets against the campaign rule plugin before Pydantic."""
    normalized = deepcopy(document)

    mechanics = normalized.get("system_mechanics")
    if not _is_typed_system_mechanics(mechanics):
        return normalized

    typed = TypedSystemMechanics.model_validate(mechanics)

    if entity_type == EntityType.PC:
        validated_sheet = validate_pc_sheet_for_campaign(campaign_game_system, typed)
    elif entity_type == EntityType.NPC:
        power_scale = "medium"
        if isinstance(mechanics, dict) and isinstance(mechanics.get("power_scale"), str):
            power_scale = mechanics["power_scale"]
        elif isinstance(mechanics, dict) and isinstance(mechanics.get("system_name"), str):
            power_scale = mechanics["system_name"]
        validated_sheet = validate_npc_sheet_for_campaign(
            campaign_game_system,
            typed,
            power_scale=power_scale,
        )
    else:
        return normalized

    normalized["system_mechanics"] = {
        "system_id": typed.system_id,
        "schema_version": typed.schema_version,
        "sheet": validated_sheet,
    }
    metadata = normalized.get("metadata")
    if isinstance(metadata, dict):
        metadata["system_agnostic"] = False
        metadata["mechanics_enabled"] = True

    return sync_combat_state_flags_from_hp(normalized)


def validate_entity_document(entity_type: EntityType, document: dict) -> BaseModel:
    model_cls = ENTITY_DOCUMENT_MODELS[entity_type]
    try:
        validated = model_cls.model_validate(document)
    except ValidationError as exc:
        raise EntityValidationError(_format_validation_error(exc)) from exc

    metadata_type = document.get("metadata", {}).get("type")
    if metadata_type != entity_type.value:
        raise EntityValidationError(
            f"document.metadata.type ({metadata_type!r}) must match entity_type ({entity_type.value!r})"
        )

    return validated


def validate_npc_sheet_for_campaign(
    campaign_game_system: str | None,
    system_mechanics: TypedSystemMechanics,
    *,
    power_scale: str = "medium",
) -> dict[str, Any]:
    plugin = get_plugin(campaign_game_system)
    expected_system_id = plugin.system_id if campaign_game_system else "generic"

    if system_mechanics.system_id != expected_system_id:
        raise EntityValidationError(
            f"system_mechanics.system_id ({system_mechanics.system_id!r}) "
            f"must match campaign game system ({expected_system_id!r})"
        )

    sheet = system_mechanics.sheet
    if not sheet:
        sheet = plugin.default_npc_sheet(power_scale)

    try:
        validated = plugin.validate_npc_sheet(sheet)
    except ValidationError as exc:
        raise EntityValidationError(
            _format_validation_error(exc, prefix="system_mechanics.sheet.")
        ) from exc
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc

    if isinstance(validated, BaseModel):
        return validated.model_dump(mode="json", by_alias=True)
    if isinstance(validated, dict):
        return validated
    raise EntityValidationError("validate_npc_sheet must return a dict or BaseModel")


def validate_pc_sheet_for_campaign(
    campaign_game_system: str | None,
    system_mechanics: TypedSystemMechanics,
) -> dict[str, Any]:
    plugin = get_plugin(campaign_game_system)
    expected_system_id = plugin.system_id if campaign_game_system else "generic"

    if system_mechanics.system_id != expected_system_id:
        raise EntityValidationError(
            f"system_mechanics.system_id ({system_mechanics.system_id!r}) "
            f"must match campaign game system ({expected_system_id!r})"
        )

    sheet = system_mechanics.sheet
    if not sheet:
        sheet = plugin.default_pc_sheet()

    try:
        validated = plugin.validate_pc_sheet(sheet)
    except ValidationError as exc:
        raise EntityValidationError(
            _format_validation_error(exc, prefix="system_mechanics.sheet.")
        ) from exc
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc

    if isinstance(validated, BaseModel):
        return validated.model_dump(mode="json", by_alias=True)
    if isinstance(validated, dict):
        return validated
    raise EntityValidationError("validate_pc_sheet must return a dict or BaseModel")


def build_pc_document(
    *,
    user_id: str,
    payload: CharacterSheetUpsert,
    validated_sheet: dict[str, Any],
    existing: CampaignEntity | None = None,
) -> dict[str, Any]:
    state_flags = payload.state_flags or PCStateFlags(
        is_present_in_scene=False,
        is_incapacitated=False,
    )
    if existing is not None:
        existing_flags = existing.document.get("state_flags", {})
        if payload.state_flags is None and isinstance(existing_flags, dict):
            state_flags = PCStateFlags.model_validate(existing_flags)

    document: dict[str, Any] = {
        "metadata": {
            "type": "PC",
            "system_agnostic": False,
            "version": "1.0.0",
        },
        "identity": payload.identity.model_dump(mode="json"),
        "player_binding": {
            "user_id": user_id,
            "is_active_in_campaign": True,
        },
        "system_mechanics": {
            "system_id": payload.system_mechanics.system_id,
            "schema_version": payload.system_mechanics.schema_version,
            "sheet": validated_sheet,
        },
        "state_flags": state_flags.model_dump(mode="json"),
    }
    if payload.public_profile is not None:
        document["public_profile"] = payload.public_profile.model_dump(mode="json")
    return document


def strip_master_secrets(document: dict, entity_type: EntityType) -> dict:
    """Remove master-only fields before exposing documents to players."""
    sanitized = deepcopy(document)

    if entity_type == EntityType.NPC:
        profile = sanitized.get("ai_narrative_profile")
        if isinstance(profile, dict):
            profile.pop("secret_lore_master", None)
    elif entity_type in (EntityType.FACTION, EntityType.LOCATION):
        profile = sanitized.get("narrative_profile")
        if isinstance(profile, dict):
            profile.pop("secret_lore_master", None)
    elif entity_type == EntityType.RELATIONSHIP:
        bond = sanitized.get("narrative_bond")
        if isinstance(bond, dict):
            bond.pop("secret_nuance", None)
    elif entity_type == EntityType.ARC_MANIFEST:
        for quest in sanitized.get("active_quests", []):
            if isinstance(quest, dict):
                quest.pop("secret_dm_notes", None)

    return sanitized


HIDDEN_NPC_DISPLAY_NAME = "Desconocido"
HIDDEN_NPC_PLACEHOLDER = "?????"


def mask_hidden_npc_document(document: dict) -> dict:
    """Strip identity and lore from NPCs hidden from players in the active scene."""
    sanitized = deepcopy(document)

    identity = sanitized.get("identity")
    if isinstance(identity, dict):
        identity["name"] = HIDDEN_NPC_DISPLAY_NAME
        identity["concept"] = HIDDEN_NPC_PLACEHOLDER

    profile = sanitized.get("ai_narrative_profile")
    if isinstance(profile, dict):
        profile["public_description"] = HIDDEN_NPC_PLACEHOLDER
        profile["personality_traits"] = []
        profile["voice_and_tone"] = HIDDEN_NPC_PLACEHOLDER
        profile.pop("secret_lore_master", None)
        profile.pop("avatar_url", None)
        profile.pop("illustration_url", None)

    mechanics = sanitized.get("system_mechanics")
    if isinstance(mechanics, dict):
        if "sheet" in mechanics:
            mechanics["sheet"] = {}
        mechanics["stats_summary"] = {}
        mechanics["notable_features"] = []

    return sanitized


def npc_player_visibility(document: dict) -> str:
    flags = document.get("state_flags")
    if not isinstance(flags, dict):
        return "visible"
    visibility = flags.get("player_visibility")
    if visibility in ("hidden", "unknown", "visible"):
        return visibility
    if bool(flags.get("hidden_from_players")):
        return "hidden"
    return "visible"


def npc_world_hidden_from_players(document: dict) -> bool:
    return npc_player_visibility(document) == "hidden"


def npc_unknown_to_players(document: dict) -> bool:
    return npc_player_visibility(document) == "unknown"


async def get_world_hidden_npc_ids(db: AsyncSession, campaign_id: uuid.UUID) -> set[str]:
    npcs = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.entity_type == EntityType.NPC.value,
            )
        )
    ).all()
    return {str(npc.id) for npc in npcs if npc_world_hidden_from_players(npc.document)}


async def get_world_unknown_npc_ids(db: AsyncSession, campaign_id: uuid.UUID) -> set[str]:
    npcs = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.entity_type == EntityType.NPC.value,
            )
        )
    ).all()
    return {str(npc.id) for npc in npcs if npc_unknown_to_players(npc.document)}


async def get_effective_hidden_npc_ids(
    db: AsyncSession,
    campaign_id: uuid.UUID,
) -> set[str]:
    return await get_world_hidden_npc_ids(db, campaign_id)


async def get_effective_unknown_npc_ids(
    db: AsyncSession,
    campaign_id: uuid.UUID,
) -> set[str]:
    return await get_world_unknown_npc_ids(db, campaign_id)


async def resolve_roll_visibility(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    master_only: bool,
    sender_role: str,
    entity_id: str | None = None,
) -> str:
    if master_only and sender_role == "MASTER":
        return "master_only"
    if entity_id:
        hidden_ids = await get_effective_hidden_npc_ids(db, campaign_id)
        if entity_id in hidden_ids:
            return "master_only"
    return "all"


async def get_active_scene_hidden_npc_ids(
    db: AsyncSession,
    campaign_id: uuid.UUID,
) -> set[str]:
    from app.services.scenes import get_active_scene, load_scene_state

    scene = await get_active_scene(db, campaign_id)
    if scene is None:
        return set()
    state = load_scene_state(scene)
    return set(state.context.hidden_npc_ids)


async def set_pc_present_in_scene(
    db: AsyncSession,
    entity: CampaignEntity,
    *,
    present: bool,
    commit: bool = True,
) -> CampaignEntity:
    if entity.entity_type != EntityType.PC.value:
        raise CharacterSheetError("Only player characters support scene presence")

    document = deepcopy(entity.document)
    flags = document.get("state_flags", {})
    if not isinstance(flags, dict):
        flags = {}
    flags["is_present_in_scene"] = present
    document["state_flags"] = flags
    entity.document = document

    if commit:
        await db.commit()
        await db.refresh(entity)
    return entity


async def find_pc_by_user(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CampaignEntity | None:
    user_id_str = str(user_id)
    entities = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.entity_type == EntityType.PC.value,
                CampaignEntity.document["player_binding"]["user_id"].as_string() == user_id_str,
            )
        )
    ).all()
    if len(entities) > 1:
        raise CharacterSheetError("Multiple player characters found for this user in the campaign")
    return entities[0] if entities else None


async def list_campaign_pc_sheets(db: AsyncSession, campaign_id: uuid.UUID) -> list[CampaignEntity]:
    return list(
        await db.scalars(
            select(CampaignEntity)
            .where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.entity_type == EntityType.PC.value,
            )
            .order_by(CampaignEntity.created_at)
        )
    )


async def get_campaign_or_error(db: AsyncSession, campaign_id: uuid.UUID) -> Campaign:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        raise CharacterSheetError("Campaign not found")
    return campaign


INSPIRATION_GRANT_FORBIDDEN = "Only the master can grant inspiration"


def _sheet_inspiration_flag(sheet: dict[str, Any]) -> bool:
    roleplay = sheet.get("roleplay")
    if isinstance(roleplay, dict) and isinstance(roleplay.get("inspiration"), bool):
        return roleplay["inspiration"]
    return False


def assert_player_may_set_inspiration(
    *,
    existing: CampaignEntity | None,
    new_sheet: dict[str, Any],
) -> None:
    """Players may spend inspiration (true -> false) but never grant it (false -> true)."""
    new_inspiration = _sheet_inspiration_flag(new_sheet)
    if existing is None:
        if new_inspiration:
            raise CharacterSheetError(INSPIRATION_GRANT_FORBIDDEN)
        return

    old_sheet = existing.document.get("system_mechanics", {})
    if isinstance(old_sheet, dict):
        old_sheet = old_sheet.get("sheet")
    if not isinstance(old_sheet, dict):
        old_sheet = {}

    if not _sheet_inspiration_flag(old_sheet) and new_inspiration:
        raise CharacterSheetError(INSPIRATION_GRANT_FORBIDDEN)


async def upsert_player_character_sheet(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: CharacterSheetUpsert,
) -> CampaignEntity:
    campaign = await get_campaign_or_error(db, campaign_id)
    validated_sheet = validate_pc_sheet_for_campaign(campaign.game_system, payload.system_mechanics)
    existing = await find_pc_by_user(db, campaign_id, user_id)
    assert_player_may_set_inspiration(existing=existing, new_sheet=validated_sheet)

    document = build_pc_document(
        user_id=str(user_id),
        payload=payload,
        validated_sheet=validated_sheet,
        existing=existing,
    )

    try:
        validated = validate_entity_document(EntityType.PC, document)
    except EntityValidationError as exc:
        raise CharacterSheetError(str(exc)) from exc

    document_json = sync_combat_state_flags_from_hp(validated.model_dump(mode="json"))

    try:
        await validate_entity_cross_references(
            db,
            campaign_id=campaign_id,
            entity_type=EntityType.PC,
            document=document_json,
            entity_id=existing.id if existing is not None else None,
        )
    except EntityReferenceError as exc:
        raise CharacterSheetError(str(exc)) from exc

    if existing is not None:
        bound_user = existing.document.get("player_binding", {}).get("user_id")
        if bound_user != str(user_id):
            raise CharacterSheetError("Cannot modify another player's character sheet")
        existing.document = document_json
        await db.commit()
        await db.refresh(existing)
        return existing

    entity = CampaignEntity(
        campaign_id=campaign_id,
        entity_type=EntityType.PC.value,
        document=document_json,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)

    from app.services.scenes import add_player_to_scene_presence, get_active_scene

    active_scene = await get_active_scene(db, campaign_id)
    if active_scene is not None and active_scene.status == "ACTIVE":
        await add_player_to_scene_presence(db, active_scene, entity_id=entity.id)

    return entity


def _persist_death_save_roll_to_entity(entity: CampaignEntity, roll_result: dict[str, Any]) -> None:
    if roll_result.get("roll_type") != "death_save":
        return
    roll_details = roll_result.get("roll_details")
    if not isinstance(roll_details, dict):
        return

    document = deepcopy(entity.document)
    system_mechanics = document.get("system_mechanics", {})
    if not isinstance(system_mechanics, dict):
        return
    sheet = system_mechanics.get("sheet")
    if not isinstance(sheet, dict):
        return

    updated_sheet = deepcopy(sheet)
    successes = roll_details.get("death_save_successes")
    failures = roll_details.get("death_save_failures")
    hp_current = roll_details.get("hp_current")

    if isinstance(updated_sheet.get("defense"), dict):
        if isinstance(successes, int):
            updated_sheet["defense"].setdefault("death_saves", {})["successes"] = successes
        if isinstance(failures, int):
            updated_sheet["defense"].setdefault("death_saves", {})["failures"] = failures
        if isinstance(hp_current, int):
            updated_sheet["defense"].setdefault("hp", {})["current"] = hp_current

    if isinstance(successes, int):
        updated_sheet.setdefault("death_saves", {})["successes"] = successes
    if isinstance(failures, int):
        updated_sheet.setdefault("death_saves", {})["failures"] = failures
    if isinstance(hp_current, int):
        updated_sheet.setdefault("hp", {})["current"] = hp_current

    system_mechanics["sheet"] = updated_sheet
    document["system_mechanics"] = system_mechanics

    flags = document.get("state_flags", {})
    if not isinstance(flags, dict):
        flags = {}
    if roll_details.get("dead"):
        flags["is_dead"] = True
        flags["is_incapacitated"] = True
    elif isinstance(hp_current, int) and hp_current > 0:
        flags["is_incapacitated"] = False
        flags["is_dead"] = False
    document["state_flags"] = flags

    entity.document = document


async def roll_player_character_contextual(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    roll_type: str,
    dice_expression: str = "1d20",
    modifier: int = 0,
    context: dict[str, Any] | None = None,
    sender_role: str = "PLAYER",
    master_only: bool = False,
) -> tuple[dict[str, Any], str | None]:
    """Roll from character sheet. Returns (roll_result, active_scene_id or None)."""
    campaign = await get_campaign_or_error(db, campaign_id)
    pc = await find_pc_by_user(db, campaign_id, user_id)
    if pc is None:
        raise CharacterSheetError("Character sheet not found")

    sheet = pc.document.get("system_mechanics", {}).get("sheet")
    if not isinstance(sheet, dict):
        raise CharacterSheetError("Character sheet has no valid system mechanics")

    try:
        roll_result = roll_dice(
            dice_expression,
            modifier,
            game_system=campaign.game_system,
            sheet=sheet,
            roll_type=roll_type,
            context=context or {},
        )
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc

    _persist_death_save_roll_to_entity(pc, roll_result)
    await db.commit()
    await db.refresh(pc)

    from app.services.scenes import append_dice_roll_to_scene, get_active_scene

    active_scene = await get_active_scene(db, campaign_id)
    scene_id: str | None = None
    if active_scene is not None and active_scene.status == "ACTIVE":
        roll_details = roll_result.get("roll_details")
        skill_checked = None
        if isinstance(roll_details, dict):
            roll_label = roll_details.get("roll_label")
            if isinstance(roll_label, str) and roll_label.strip():
                skill_checked = roll_label.strip()
        if skill_checked is None and context and isinstance(context.get("skill"), str):
            skill_checked = context["skill"]
        master_only = master_only and sender_role == "MASTER"
        visibility = await resolve_roll_visibility(
            db,
            campaign_id,
            master_only=master_only,
            sender_role=sender_role,
            entity_id=str(pc.id),
        )
        await append_dice_roll_to_scene(
            db,
            active_scene,
            sender_id=str(user_id),
            roll_result=roll_result,
            entity_id=str(pc.id),
            skill_checked=skill_checked,
            visibility=visibility,
            sender_role=sender_role,
        )
        scene_id = str(active_scene.id)

    return roll_result, scene_id


async def roll_entity_contextual(
    db: AsyncSession,
    *,
    entity: CampaignEntity,
    sender_id: str,
    sender_role: str,
    roll_type: str,
    dice_expression: str = "1d20",
    modifier: int = 0,
    context: dict[str, Any] | None = None,
    master_only: bool = False,
) -> tuple[dict[str, Any], str | None]:
    """Roll from an entity sheet (master: NPC; member: own PC). Returns (roll_result, scene_id)."""
    campaign = await get_campaign_or_error(db, entity.campaign_id)

    if entity.entity_type == EntityType.NPC.value:
        if sender_role != "MASTER":
            raise CharacterSheetError("Only the master can roll for NPCs")
    elif entity.entity_type == EntityType.PC.value:
        binding = entity.document.get("player_binding", {})
        if sender_role != "MASTER" and (
            not isinstance(binding, dict) or binding.get("user_id") != sender_id
        ):
            raise CharacterSheetError("You can only roll for your own character")
    else:
        raise CharacterSheetError("Only PC and NPC entities support contextual rolls")

    sheet = entity.document.get("system_mechanics", {}).get("sheet")
    if not isinstance(sheet, dict):
        raise CharacterSheetError("Entity has no valid system mechanics")

    try:
        roll_result = roll_dice(
            dice_expression,
            modifier,
            game_system=campaign.game_system,
            sheet=sheet,
            roll_type=roll_type,
            context=context or {},
        )
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc

    _persist_death_save_roll_to_entity(entity, roll_result)
    await db.commit()
    await db.refresh(entity)

    from app.services.scenes import append_dice_roll_to_scene, get_active_scene

    active_scene = await get_active_scene(db, entity.campaign_id)
    scene_id: str | None = None
    if active_scene is not None and active_scene.status == "ACTIVE":
        roll_details = roll_result.get("roll_details")
        skill_checked = None
        if isinstance(roll_details, dict):
            roll_label = roll_details.get("roll_label")
            if isinstance(roll_label, str) and roll_label.strip():
                skill_checked = roll_label.strip()
        if skill_checked is None and context and isinstance(context.get("skill"), str):
            skill_checked = context["skill"]
        visibility = await resolve_roll_visibility(
            db,
            entity.campaign_id,
            master_only=master_only,
            sender_role=sender_role,
            entity_id=str(entity.id),
        )
        await append_dice_roll_to_scene(
            db,
            active_scene,
            sender_id=sender_id,
            roll_result=roll_result,
            entity_id=str(entity.id),
            skill_checked=skill_checked,
            visibility=visibility,
            sender_role=sender_role,
        )
        scene_id = str(active_scene.id)

    return roll_result, scene_id

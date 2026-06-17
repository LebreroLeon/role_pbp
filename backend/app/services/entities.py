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

    return normalized


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
        return validated.model_dump(mode="json")
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
        return validated.model_dump(mode="json")
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

    mechanics = sanitized.get("system_mechanics")
    if isinstance(mechanics, dict):
        if "sheet" in mechanics:
            mechanics["sheet"] = {}
        mechanics["stats_summary"] = {}
        mechanics["notable_features"] = []

    return sanitized


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

    document_json = validated.model_dump(mode="json")

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
    return entity


async def roll_player_character_contextual(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    roll_type: str,
    dice_expression: str = "1d20",
    modifier: int = 0,
    context: dict[str, Any] | None = None,
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

    from app.services.scenes import append_dice_roll_to_scene, get_active_scene

    active_scene = await get_active_scene(db, campaign_id)
    scene_id: str | None = None
    if active_scene is not None and active_scene.status == "ACTIVE":
        skill_checked = None
        if context and isinstance(context.get("skill"), str):
            skill_checked = context["skill"]
        await append_dice_roll_to_scene(
            db,
            active_scene,
            sender_id=str(user_id),
            roll_result=roll_result,
            entity_id=str(pc.id),
            skill_checked=skill_checked,
        )
        scene_id = str(active_scene.id)

    return roll_result, scene_id

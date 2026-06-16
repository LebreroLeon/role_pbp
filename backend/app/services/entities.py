from copy import deepcopy

from pydantic import BaseModel, ValidationError

from app.schemas.entities import ENTITY_DOCUMENT_MODELS, EntityType


class EntityValidationError(ValueError):
    pass


def validate_entity_document(entity_type: EntityType, document: dict) -> BaseModel:
    model_cls = ENTITY_DOCUMENT_MODELS[entity_type]
    try:
        validated = model_cls.model_validate(document)
    except ValidationError as exc:
        raise EntityValidationError(str(exc)) from exc

    metadata_type = document.get("metadata", {}).get("type")
    if metadata_type != entity_type.value:
        raise EntityValidationError(
            f"document.metadata.type ({metadata_type!r}) must match entity_type ({entity_type.value!r})"
        )

    return validated


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

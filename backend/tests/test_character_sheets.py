import uuid

import pytest
from pydantic import ValidationError

from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.entities import EntityType, TypedSystemMechanics
from app.services.entities import (
    EntityValidationError,
    normalize_entity_document_for_campaign,
    strip_master_secrets,
    validate_entity_document,
    validate_npc_sheet_for_campaign,
)


def _npc_document_with_typed_sheet(sheet: dict | None = None) -> dict:
    resolved_sheet = sheet or Dnd5ePlugin().default_npc_sheet("medium")
    return {
        "metadata": {"type": "NPC", "system_agnostic": False, "mechanics_enabled": True, "version": "2.0.0"},
        "identity": {
            "name": "Goblin",
            "concept": "Skulker",
            "faction_id": "00000000-0000-0000-0000-000000000001",
            "current_location_id": "00000000-0000-0000-0000-000000000001",
        },
        "ai_narrative_profile": {
            "public_description": "A small green humanoid",
            "secret_lore_master": "Leader of the hidden tribe",
            "personality_traits": ["cowardly"],
            "voice_and_tone": "squeaky",
        },
        "system_mechanics": {
            "system_id": "dnd5e",
            "schema_version": "1.0.0",
            "sheet": resolved_sheet,
        },
        "state_flags": {
            "is_dead": False,
            "is_present_in_scene": False,
            "attitude_towards_party": "neutral",
            "has_met_party": False,
        },
    }


class TestNpcSheetValidation:
    def test_validate_npc_sheet_for_campaign(self):
        mechanics = TypedSystemMechanics(system_id="dnd5e", schema_version="1.0.0", sheet={})
        validated = validate_npc_sheet_for_campaign("dnd5e", mechanics)
        assert "hp" in validated

    def test_validate_npc_sheet_rejects_wrong_system(self):
        mechanics = TypedSystemMechanics(system_id="vtm_v5", schema_version="1.0.0", sheet={})
        with pytest.raises(EntityValidationError, match="must match campaign game system"):
            validate_npc_sheet_for_campaign("dnd5e", mechanics)

    def test_normalize_npc_document_and_validate(self):
        document = _npc_document_with_typed_sheet()
        normalized = normalize_entity_document_for_campaign(
            campaign_game_system="dnd5e",
            entity_type=EntityType.NPC,
            document=document,
        )
        validated = validate_entity_document(EntityType.NPC, normalized)
        dumped = validated.model_dump(mode="json")
        assert dumped["metadata"]["system_agnostic"] is False
        assert dumped["system_mechanics"]["system_id"] == "dnd5e"

    def test_strip_master_secrets_removes_npc_lore(self):
        document = _npc_document_with_typed_sheet()
        sanitized = strip_master_secrets(document, EntityType.NPC)
        assert "secret_lore_master" not in sanitized["ai_narrative_profile"]

    def test_legacy_agnostic_npc_still_validates(self):
        document = {
            "metadata": {"type": "NPC", "system_agnostic": True, "version": "2.0.0"},
            "identity": {
                "name": "Innkeeper",
                "concept": "Friendly",
                "faction_id": str(uuid.uuid4()),
                "current_location_id": str(uuid.uuid4()),
            },
            "ai_narrative_profile": {
                "public_description": "Runs the tavern",
                "secret_lore_master": "Smuggler",
                "personality_traits": ["cheerful"],
                "voice_and_tone": "warm",
            },
            "system_mechanics": {
                "system_name": "agnóstico",
                "power_scale": "weak",
                "stats_summary": {},
                "notable_features": [],
            },
            "state_flags": {
                "is_dead": False,
                "is_present_in_scene": False,
                "attitude_towards_party": "friendly",
                "has_met_party": True,
            },
        }
        validated = validate_entity_document(EntityType.NPC, document)
        assert validated.metadata.system_agnostic is True

    def test_typed_npc_rejects_invalid_sheet(self):
        document = _npc_document_with_typed_sheet({"hp": "not-a-sheet"})
        with pytest.raises(EntityValidationError):
            normalize_entity_document_for_campaign(
                campaign_game_system="dnd5e",
                entity_type=EntityType.NPC,
                document=document,
            )

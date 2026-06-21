"""Tests for unified NPC player_visibility states."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.campaign import CampaignEntity
from app.schemas.entities import EntityType
from app.services.entities import (
    HIDDEN_NPC_DISPLAY_NAME,
    get_effective_hidden_npc_ids,
    mask_hidden_npc_document,
    npc_player_visibility,
    npc_unknown_to_players,
    npc_world_hidden_from_players,
    resolve_roll_visibility,
    validate_entity_document,
)


def _npc_document(*, visibility: str = "visible", name: str = "Arturo") -> dict:
    hidden = visibility == "hidden"
    return {
        "metadata": {"type": "NPC", "system_agnostic": True, "version": "2.0.0"},
        "identity": {"name": name, "concept": "Spy"},
        "ai_narrative_profile": {
            "public_description": "Shady",
            "secret_lore_master": "Secret",
            "personality_traits": ["quiet"],
            "voice_and_tone": "whisper",
        },
        "system_mechanics": {
            "system_name": "agnóstico",
            "power_scale": "medium",
            "stats_summary": {},
            "notable_features": [],
        },
        "state_flags": {
            "is_dead": False,
            "is_present_in_scene": False,
            "attitude_towards_party": "neutral",
            "has_met_party": False,
            "player_visibility": visibility,
            "hidden_from_players": hidden,
        },
    }


class TestNpcPlayerVisibility:
    def test_reads_canonical_field(self):
        assert npc_player_visibility(_npc_document(visibility="unknown")) == "unknown"

    def test_legacy_hidden_from_players_maps_to_hidden(self):
        document = _npc_document(visibility="visible")
        document["state_flags"].pop("player_visibility")
        document["state_flags"]["hidden_from_players"] = True
        assert npc_player_visibility(document) == "hidden"

    def test_schema_normalizes_visibility(self):
        validated = validate_entity_document(EntityType.NPC, _npc_document(visibility="unknown"))
        assert validated.state_flags.player_visibility == "unknown"
        assert validated.state_flags.hidden_from_players is False

    def test_hidden_syncs_legacy_flag(self):
        validated = validate_entity_document(EntityType.NPC, _npc_document(visibility="hidden"))
        assert validated.state_flags.hidden_from_players is True

    def test_unknown_is_not_world_hidden(self):
        document = _npc_document(visibility="unknown")
        assert npc_world_hidden_from_players(document) is False
        assert npc_unknown_to_players(document) is True

    def test_mask_unknown_npc_document(self):
        masked = mask_hidden_npc_document(_npc_document(visibility="unknown", name="Arturo"))
        assert masked["identity"]["name"] == HIDDEN_NPC_DISPLAY_NAME


class TestHiddenNpcRolls:
    def test_only_fully_hidden_npc_rolls_are_master_only(self):
        async def run():
            campaign_id = uuid.uuid4()
            hidden_npc = CampaignEntity(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                entity_type="NPC",
                document=_npc_document(visibility="hidden"),
            )
            unknown_npc = CampaignEntity(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                entity_type="NPC",
                document=_npc_document(visibility="unknown"),
            )

            db = AsyncMock()

            async def scalars_side_effect(stmt):
                result = MagicMock()
                result.all = lambda: [hidden_npc, unknown_npc]
                return result

            db.scalars = AsyncMock(side_effect=scalars_side_effect)

            hidden_visibility = await resolve_roll_visibility(
                db,
                campaign_id,
                master_only=False,
                sender_role="MASTER",
                entity_id=str(hidden_npc.id),
            )
            unknown_visibility = await resolve_roll_visibility(
                db,
                campaign_id,
                master_only=False,
                sender_role="MASTER",
                entity_id=str(unknown_npc.id),
            )

            assert hidden_visibility == "master_only"
            assert unknown_visibility == "all"

        asyncio.run(run())

    def test_effective_hidden_ids_only_includes_hidden(self):
        async def run():
            campaign_id = uuid.uuid4()
            hidden_npc = CampaignEntity(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                entity_type="NPC",
                document=_npc_document(visibility="hidden"),
            )
            unknown_npc = CampaignEntity(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                entity_type="NPC",
                document=_npc_document(visibility="unknown"),
            )

            db = AsyncMock()

            async def scalars_side_effect(stmt):
                result = MagicMock()
                result.all = lambda: [hidden_npc, unknown_npc]
                return result

            db.scalars = AsyncMock(side_effect=scalars_side_effect)

            hidden_ids = await get_effective_hidden_npc_ids(db, campaign_id)
            assert hidden_ids == {str(hidden_npc.id)}

        asyncio.run(run())

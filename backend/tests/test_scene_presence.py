import asyncio
import uuid
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.campaign import CampaignEntity, Scene
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.scene import InitiativeEntry, NpcPresenceEntry, SceneContext, SceneMetadata, ScenePresenceUpdate, SceneState, StateFlags
from app.services.combat_resolver import fetch_scene_combat_entities, resolve_entity_reference
from app.services.entities import (
    HIDDEN_NPC_DISPLAY_NAME,
    mask_hidden_npc_document,
    set_pc_present_in_scene,
)
from app.services.scenes import (
    _apply_npc_presence_to_state,
    build_dice_roll_message,
    load_scene_state,
    update_scene_npc_presence,
)


def _make_pc(*, name: str, present: bool = False, user_id: str = "player-1") -> CampaignEntity:
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        entity_type="PC",
        document={
            "identity": {"name": name},
            "player_binding": {"user_id": user_id},
            "system_mechanics": {
                "system_id": "dnd5e",
                "schema_version": "1.0.0",
                "sheet": Dnd5ePlugin().default_pc_sheet(),
            },
            "state_flags": {"is_present_in_scene": present, "is_incapacitated": False},
        },
    )


def _make_npc(*, name: str) -> CampaignEntity:
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        entity_type="NPC",
        document={
            "identity": {"name": name, "concept": "Spy", "faction_id": "x", "current_location_id": "y"},
            "ai_narrative_profile": {
                "public_description": "A shady figure",
                "secret_lore_master": "Actually the king",
                "personality_traits": ["quiet"],
                "voice_and_tone": "whisper",
            },
            "system_mechanics": {
                "system_name": "dnd5e",
                "power_scale": "medium",
                "stats_summary": {"hp": "10"},
                "notable_features": ["cloak"],
            },
            "state_flags": {
                "is_dead": False,
                "is_present_in_scene": False,
                "attitude_towards_party": "neutral",
                "has_met_party": False,
            },
        },
    )


class TestNpcPresenceState:
    def test_add_visible_and_hidden_npcs(self):
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
        )
        npc_visible = str(uuid.uuid4())
        npc_hidden = str(uuid.uuid4())

        _apply_npc_presence_to_state(
            state,
            add=[
                NpcPresenceEntry(entity_id=npc_visible, is_hidden_from_players=False),
                NpcPresenceEntry(entity_id=npc_hidden, is_hidden_from_players=True),
            ],
            remove=[],
        )

        assert state.context.active_npc_ids == [npc_visible, npc_hidden]
        assert state.context.hidden_npc_ids == [npc_hidden]

    def test_remove_npc_clears_hidden_flag(self):
        npc_id = str(uuid.uuid4())
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[npc_id], hidden_npc_ids=[npc_id]),
        )

        _apply_npc_presence_to_state(state, add=[], remove=[npc_id])

        assert state.context.active_npc_ids == []
        assert state.context.hidden_npc_ids == []

    def test_reveal_npc_updates_hidden_list(self):
        npc_id = str(uuid.uuid4())
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[npc_id], hidden_npc_ids=[npc_id]),
        )

        _apply_npc_presence_to_state(
            state,
            add=[NpcPresenceEntry(entity_id=npc_id, is_hidden_from_players=False)],
            remove=[],
        )

        assert npc_id in state.context.active_npc_ids
        assert state.context.hidden_npc_ids == []


class TestHiddenNpcMasking:
    def test_mask_npc_document_for_players(self):
        npc = _make_npc(name="Arturo")
        masked = mask_hidden_npc_document(npc.document)

        assert masked["identity"]["name"] == HIDDEN_NPC_DISPLAY_NAME
        assert masked["identity"]["concept"] == "?????"
        assert masked["ai_narrative_profile"]["public_description"] == "?????"
        assert "secret_lore_master" not in masked["ai_narrative_profile"]


class TestPcPresence:
    def test_set_pc_present_in_scene(self):
        pc = _make_pc(name="Kaelen", present=False)

        db = AsyncMock()
        updated = asyncio.run(set_pc_present_in_scene(db, pc, present=True, commit=False))

        assert updated.document["state_flags"]["is_present_in_scene"] is True


class TestSceneCombatEntitiesWithPresence:
    def test_includes_present_pc_when_initiative_active(self):
        arturo = _make_pc(name="Arturo", present=True, user_id="player-2")
        norman = _make_pc(name="Norman", present=False, user_id="player-1")
        goblin = _make_npc(name="Goblin")

        db = AsyncMock()
        db.scalars = AsyncMock(
            side_effect=[
                MagicMock(all=lambda: [norman, arturo]),
                MagicMock(all=lambda: [goblin]),
            ]
        )

        campaign_id = uuid.uuid4()
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[str(goblin.id)]),
            state_flags=StateFlags(),
        )
        state.combat.initiative_order = [
            InitiativeEntry(entity_id=str(goblin.id), initiative_score=15),
        ]

        entities = asyncio.run(fetch_scene_combat_entities(db, campaign_id, state))
        names = {entity.document["identity"]["name"] for entity in entities}

        assert "Arturo" in names
        assert "Norman" not in names
        assert "Goblin" in names

    def test_resolve_name_case_insensitive(self):
        arturo = _make_pc(name="Arturo")
        resolved = resolve_entity_reference("arturo", [arturo])
        assert resolved.id == arturo.id


class TestDiceRollMessage:
    def test_build_dice_roll_message_from_sheet_roll(self):
        message = build_dice_roll_message(
            sender_id="player-1",
            roll_result={
                "dice_expression": "1d20+3",
                "raw_result": 12,
                "final_result": 15,
                "chat_summary": "Perception 15",
                "roll_type": "skill_check",
                "roll_details": {"skill": "Perception"},
            },
            entity_id="entity-1",
            skill_checked="Perception",
        )

        assert message["type"] == "DICE_ROLL"
        assert message["text"] == "Perception 15"
        assert message["entity_id"] == "entity-1"
        assert message["roll_type"] == "skill_check"


class TestUpdateSceneNpcPresence:
    def test_persists_npc_presence_to_scene(self):
        campaign_id = uuid.uuid4()
        npc = _make_npc(name="Goblin")
        npc.campaign_id = campaign_id

        scene = Scene(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            status="ACTIVE",
            scene_state=SceneState(
                metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
                context=SceneContext(),
            ).model_dump(),
        )

        db = AsyncMock()
        db.scalars = AsyncMock(return_value=MagicMock(all=lambda: [npc]))
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        payload = ScenePresenceUpdate(
            add=[NpcPresenceEntry(entity_id=str(npc.id), is_hidden_from_players=True)],
        )
        response = asyncio.run(update_scene_npc_presence(db, scene, payload))
        state = load_scene_state(scene)

        assert str(npc.id) in state.context.active_npc_ids
        assert str(npc.id) in state.context.hidden_npc_ids
        assert str(npc.id) in response.scene_state.context.active_npc_ids

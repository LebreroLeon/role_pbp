import asyncio
import uuid
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import CampaignEntity, Scene
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.scene import InitiativeEntry, NpcPresenceEntry, SceneContext, SceneMetadata, ScenePresenceUpdate, SceneState, StateFlags, TurnManagement
from app.services.combat_resolver import fetch_scene_combat_entities, resolve_entity_reference
from app.services.entities import (
    HIDDEN_NPC_DISPLAY_NAME,
    mask_hidden_npc_document,
    set_pc_present_in_scene,
)
from app.services.scenes import (
    _apply_npc_presence_to_state,
    _append_pc_to_pbp_initiative_if_needed,
    add_player_to_scene_presence,
    build_dice_roll_message,
    load_scene_state,
    mark_all_campaign_pcs_present_for_scene,
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

    def test_visible_npc_not_hidden_even_if_never_met_party(self):
        """Scene visibility is driven by hidden_npc_ids, not entity has_met_party."""
        npc_id = str(uuid.uuid4())
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
        )

        _apply_npc_presence_to_state(
            state,
            add=[NpcPresenceEntry(entity_id=npc_id, is_hidden_from_players=False)],
            remove=[],
        )

        assert state.context.active_npc_ids == [npc_id]
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
                "rolls": [12],
                "raw_result": 12,
                "final_result": 15,
                "chat_summary": "Percepción: 1d20=12 +3 = 15",
                "roll_type": "skill_check",
                "roll_details": {
                    "skill": "Perception",
                    "roll_label": "Percepción",
                    "modifier_breakdown": [
                        {"label": "Sabiduría", "value": 0},
                        {"label": "Competencia", "value": 2},
                    ],
                },
            },
            entity_id="entity-1",
            skill_checked="Percepción",
        )

        assert message["type"] == "DICE_ROLL"
        assert message["text"] == "Percepción: 1d20=12 +3 = 15"
        assert message["entity_id"] == "entity-1"
        assert message["roll_type"] == "skill_check"
        assert message["rolls"] == [12]
        assert message["chat_summary"] == "Percepción: 1d20=12 +3 = 15"
        assert message["skill_checked"] == "Percepción"
        assert message["roll_details"]["roll_label"] == "Percepción"


class TestUpdateSceneNpcPresence:
    def test_persists_npc_presence_to_scene(self):
        campaign_id = uuid.uuid4()
        npc = _make_npc(name="Goblin")
        npc.campaign_id = campaign_id

        scene = Scene(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            scene_number=1,
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


class TestPcScenePresence:
    def test_mark_all_campaign_pcs_present(self):
        campaign_id = uuid.uuid4()
        pc_a = _make_pc(name="Arturo", present=False, user_id="player-1")
        pc_b = _make_pc(name="Norman", present=False, user_id="player-2")
        pc_a.campaign_id = campaign_id
        pc_b.campaign_id = campaign_id

        scene = Scene(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            scene_number=1,
            status="ACTIVE",
            scene_state=SceneState(
                metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
                context=SceneContext(),
            ).model_dump(),
        )

        db = AsyncMock()
        db.scalars = AsyncMock(return_value=MagicMock(all=lambda: [pc_a, pc_b]))
        db.commit = AsyncMock()

        asyncio.run(mark_all_campaign_pcs_present_for_scene(db, scene))

        assert pc_a.document["state_flags"]["is_present_in_scene"] is True
        assert pc_b.document["state_flags"]["is_present_in_scene"] is True
        db.commit.assert_awaited_once()

    def test_add_player_appends_to_pbp_initiative(self):
        campaign_id = uuid.uuid4()
        user_id = str(uuid.uuid4())
        pc = _make_pc(name="Latecomer", present=False, user_id=user_id)
        pc.campaign_id = campaign_id
        existing = _make_pc(name="Veteran", present=True, user_id=str(uuid.uuid4()))
        existing.campaign_id = campaign_id

        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(pbp_enabled=True, order_source="manual"),
        )
        state.combat.initiative_order = [
            InitiativeEntry(entity_id=str(existing.id), entity_type="PC", display_name="Veteran"),
        ]

        scene = Scene(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            scene_number=1,
            status="ACTIVE",
            scene_state=state.model_dump(),
        )

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=pc)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch(
            "app.services.scenes.sync_turn_management_from_initiative",
            new=AsyncMock(),
        ):
            response = asyncio.run(add_player_to_scene_presence(db, scene, entity_id=pc.id))

        updated_state = load_scene_state(scene)
        initiative_ids = [entry.entity_id for entry in updated_state.combat.initiative_order]
        assert str(existing.id) in initiative_ids
        assert str(pc.id) in initiative_ids
        assert initiative_ids.index(str(pc.id)) == len(initiative_ids) - 1
        assert pc.document["state_flags"]["is_present_in_scene"] is True
        assert str(pc.id) in [
            entry.entity_id for entry in response.scene_state.combat.initiative_order
        ]

    def test_append_pc_skips_when_already_in_initiative(self):
        campaign_id = uuid.uuid4()
        pc = _make_pc(name="Arturo", present=True, user_id="player-1")
        pc.campaign_id = campaign_id

        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(pbp_enabled=True),
        )
        state.combat.initiative_order = [
            InitiativeEntry(entity_id=str(pc.id), entity_type="PC", display_name="Arturo"),
        ]

        scene = Scene(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            scene_number=1,
            status="ACTIVE",
            scene_state=state.model_dump(),
        )

        db = AsyncMock()
        asyncio.run(_append_pc_to_pbp_initiative_if_needed(db, scene, pc, state))

        assert len(state.combat.initiative_order) == 1

    def test_add_player_appends_to_user_turn_order_when_no_initiative(self):
        campaign_id = uuid.uuid4()
        user_id = str(uuid.uuid4())
        pc = _make_pc(name="Latecomer", present=False, user_id=user_id)
        pc.campaign_id = campaign_id
        veteran_user_id = str(uuid.uuid4())

        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(
                pbp_enabled=True,
                turn_order=[veteran_user_id],
                current_turn_player_id=veteran_user_id,
                order_source="manual",
            ),
        )

        scene = Scene(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            scene_number=1,
            status="ACTIVE",
            scene_state=state.model_dump(),
        )

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=pc)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        response = asyncio.run(add_player_to_scene_presence(db, scene, entity_id=pc.id))

        updated_state = load_scene_state(scene)
        assert updated_state.combat.initiative_order == []
        assert updated_state.turn_management.turn_order == [veteran_user_id, user_id]
        assert updated_state.turn_management.current_turn_player_id == veteran_user_id
        assert pc.document["state_flags"]["is_present_in_scene"] is True
        assert response.scene_state.turn_management.turn_order == [veteran_user_id, user_id]

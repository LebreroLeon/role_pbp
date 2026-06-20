"""Tests for master-only rolls and hidden NPC visibility."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.campaign import CampaignEntity, Scene
from app.schemas.scene import (
    DiceRollRequest,
    SceneContext,
    SceneMetadata,
    SceneState,
)
from app.services.entities import (
    get_effective_hidden_npc_ids,
    get_world_hidden_npc_ids,
    npc_world_hidden_from_players,
    resolve_roll_visibility,
)
from app.services.scenes import (
    build_dice_roll_message,
    filter_scene_state_for_viewer,
    load_scene_state,
    roll_scene_dice,
)


def _make_npc(*, hidden_world: bool = False, name: str = "Goblin") -> CampaignEntity:
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        entity_type="NPC",
        document={
            "identity": {"name": name, "concept": "Enemy"},
            "ai_narrative_profile": {"public_description": "A goblin"},
            "state_flags": {
                "is_dead": False,
                "is_present_in_scene": False,
                "attitude_towards_party": "hostile",
                "has_met_party": False,
                "hidden_from_players": hidden_world,
            },
        },
    )


class TestNpcWorldHidden:
    def test_npc_world_hidden_from_players_flag(self):
        npc = _make_npc(hidden_world=True)
        assert npc_world_hidden_from_players(npc.document) is True

    def test_npc_not_hidden_by_default(self):
        document = _make_npc().document
        document["state_flags"].pop("hidden_from_players", None)
        assert npc_world_hidden_from_players(document) is False


class TestResolveRollVisibility:
    def test_master_secret_roll(self):
        async def run():
            db = AsyncMock()
            visibility = await resolve_roll_visibility(
                db,
                uuid.uuid4(),
                master_only=True,
                sender_role="MASTER",
            )
            assert visibility == "master_only"

        asyncio.run(run())

    def test_player_cannot_use_master_only_flag(self):
        async def run():
            db = AsyncMock()
            visibility = await resolve_roll_visibility(
                db,
                uuid.uuid4(),
                master_only=True,
                sender_role="PLAYER",
            )
            assert visibility == "all"

        asyncio.run(run())

    def test_hidden_npc_roll_is_master_only(self):
        async def run():
            campaign_id = uuid.uuid4()
            npc = _make_npc(hidden_world=True)
            npc.campaign_id = campaign_id

            scene = Scene(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                scene_number=1,
                status="ACTIVE",
                scene_state=SceneState(
                    metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
                    context=SceneContext(active_npc_ids=[str(npc.id)], hidden_npc_ids=[str(npc.id)]),
                ).model_dump(),
            )

            db = AsyncMock()

            async def scalar_side_effect(stmt):
                return scene

            async def scalars_side_effect(stmt):
                result = MagicMock()
                result.all = lambda: [npc]
                return result

            db.scalar = AsyncMock(side_effect=scalar_side_effect)
            db.scalars = AsyncMock(side_effect=scalars_side_effect)

            visibility = await resolve_roll_visibility(
                db,
                campaign_id,
                master_only=False,
                sender_role="MASTER",
                entity_id=str(npc.id),
            )
            assert visibility == "master_only"

        asyncio.run(run())


class TestFilterSceneStateForViewer:
    def test_players_do_not_see_master_only_messages(self):
        state = SceneState(
            metadata=SceneMetadata(campaign_id="c1", status="ACTIVE"),
            chat_buffer=[
                {
                    "id": "1",
                    "timestamp": "t1",
                    "sender_id": "master",
                    "type": "DICE_ROLL",
                    "text": "Secreto",
                    "visibility": "master_only",
                },
                {
                    "id": "2",
                    "timestamp": "t2",
                    "sender_id": "master",
                    "type": "ACTION",
                    "text": "Público",
                    "visibility": "all",
                },
            ],
        )

        filtered = filter_scene_state_for_viewer(state, "PLAYER")
        assert len(filtered.chat_buffer) == 1
        assert filtered.chat_buffer[0].text == "Público"

    def test_master_sees_all_messages(self):
        state = SceneState(
            metadata=SceneMetadata(campaign_id="c1", status="ACTIVE"),
            chat_buffer=[
                {
                    "id": "1",
                    "timestamp": "t1",
                    "sender_id": "master",
                    "type": "DICE_ROLL",
                    "text": "Secreto",
                    "visibility": "master_only",
                },
            ],
        )

        filtered = filter_scene_state_for_viewer(state, "MASTER")
        assert len(filtered.chat_buffer) == 1


class TestBuildDiceRollMessage:
    def test_includes_visibility(self):
        message = build_dice_roll_message(
            sender_id="master-1",
            roll_result={"dice_expression": "1d20", "final_result": 15, "raw_result": 15},
            visibility="master_only",
        )
        assert message["visibility"] == "master_only"


class TestRollSceneDiceMasterOnly:
    def test_master_secret_dice_roll_stored_as_master_only(self):
        campaign_id = uuid.uuid4()
        scene = Scene(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            scene_number=1,
            status="ACTIVE",
            scene_state=SceneState(
                metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
            ).model_dump(),
        )

        campaign = MagicMock()
        campaign.game_system = "generic"

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with (
            pytest.MonkeyPatch.context() as mp
        ):
            mp.setattr(
                "app.services.scenes.get_campaign_or_error",
                AsyncMock(return_value=campaign),
            )
            mp.setattr(
                "app.services.scenes.assert_pbp_post_allowed",
                AsyncMock(),
            )
            mp.setattr(
                "app.services.scenes.roll_dice_expression",
                lambda *args, **kwargs: {
                    "rolls": [10],
                    "raw_result": 10,
                    "final_result": 10,
                    "chat_summary": "1d20=10",
                },
            )
            mp.setattr(
                "app.services.entities.resolve_roll_visibility",
                AsyncMock(return_value="master_only"),
            )

            asyncio.run(
                roll_scene_dice(
                    db,
                    scene,
                    "master-user",
                    DiceRollRequest(dice_expression="1d20", master_only=True),
                    sender_role="MASTER",
                )
            )

        state = load_scene_state(scene)
        assert len(state.chat_buffer) == 1
        assert state.chat_buffer[0].visibility == "master_only"

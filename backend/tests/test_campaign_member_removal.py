import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import CampaignEntity, Scene
from app.models.user import CampaignMember, User
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.scene import (
    ChatMessage,
    InitiativeEntry,
    PreparedEntityRef,
    SceneContext,
    SceneMetadata,
    SceneState,
    TurnManagement,
)
from app.services.campaigns import CampaignServiceError, remove_campaign_member
from app.services.entities import deactivate_pc_player_binding
from app.services.scenes import (
    _remove_player_from_scene_state,
    load_scene_state,
    remove_player_from_open_scenes,
)


def _make_pc(*, name: str, present: bool = True, user_id: str) -> CampaignEntity:
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        entity_type="PC",
        document={
            "identity": {"name": name},
            "player_binding": {"user_id": user_id, "is_active_in_campaign": True},
            "system_mechanics": {
                "system_id": "dnd5e",
                "schema_version": "1.0.0",
                "sheet": Dnd5ePlugin().default_pc_sheet(),
            },
            "state_flags": {"is_present_in_scene": present, "is_incapacitated": False},
        },
    )


def _scene_with_state(campaign_id: uuid.UUID, state: SceneState, *, status: str = "ACTIVE") -> Scene:
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        status=status,
        scene_state=state.model_dump(),
    )


class TestRemovePlayerFromSceneState:
    def test_removes_user_from_turn_order_and_advances_current_turn(self):
        removed_id = "player-removed"
        survivor_id = "player-survivor"
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(
                pbp_enabled=True,
                turn_order=[removed_id, survivor_id],
                current_turn_player_id=removed_id,
            ),
        )

        changed = _remove_player_from_scene_state(
            state,
            user_id=removed_id,
            entity_id=None,
        )

        assert changed is True
        assert state.turn_management.turn_order == [survivor_id]
        assert state.turn_management.current_turn_player_id == survivor_id

    def test_removes_entity_from_initiative_and_advances_current_turn(self):
        removed_entity = str(uuid.uuid4())
        survivor_entity = str(uuid.uuid4())
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(pbp_enabled=True),
        )
        state.combat.initiative_order = [
            InitiativeEntry(entity_id=removed_entity, entity_type="PC", display_name="Removed"),
            InitiativeEntry(entity_id=survivor_entity, entity_type="PC", display_name="Survivor"),
        ]
        state.combat.current_turn_entity_id = removed_entity

        changed = _remove_player_from_scene_state(
            state,
            user_id="player-removed",
            entity_id=removed_entity,
        )

        assert changed is True
        assert [entry.entity_id for entry in state.combat.initiative_order] == [survivor_entity]
        assert state.combat.current_turn_entity_id == survivor_entity

    def test_removes_prepared_entity_ref(self):
        entity_id = str(uuid.uuid4())
        other_id = str(uuid.uuid4())
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(
                prepared_entity_refs=[
                    PreparedEntityRef(entity_id=entity_id),
                    PreparedEntityRef(entity_id=other_id),
                ]
            ),
        )

        changed = _remove_player_from_scene_state(
            state,
            user_id="player-removed",
            entity_id=entity_id,
        )

        assert changed is True
        assert [ref.entity_id for ref in state.context.prepared_entity_refs] == [other_id]

    def test_preserves_chat_buffer(self):
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(
                turn_order=["player-removed", "player-survivor"],
                current_turn_player_id="player-removed",
            ),
        )
        state.chat_buffer = [
            ChatMessage(
                id="msg-1",
                timestamp="2026-01-01T00:00:00Z",
                sender_id="player-removed",
                type="SPEAK",
                text="Still here",
            )
        ]

        _remove_player_from_scene_state(
            state,
            user_id="player-removed",
            entity_id=None,
        )

        assert len(state.chat_buffer) == 1
        assert state.chat_buffer[0].text == "Still here"
        assert state.chat_buffer[0].sender_id == "player-removed"


class TestDeactivatePcPlayerBinding:
    def test_marks_pc_inactive_and_not_present(self):
        pc = _make_pc(name="Kaelen", present=True, user_id=str(uuid.uuid4()))
        db = AsyncMock()

        updated = asyncio.run(deactivate_pc_player_binding(db, pc, commit=False))

        assert updated.document["player_binding"]["is_active_in_campaign"] is False
        assert updated.document["state_flags"]["is_present_in_scene"] is False


class TestRemovePlayerFromOpenScenes:
    def test_cleans_active_and_paused_scenes(self):
        campaign_id = uuid.uuid4()
        user_id = uuid.uuid4()
        pc = _make_pc(name="Removed", present=True, user_id=str(user_id))
        pc.campaign_id = campaign_id
        survivor = _make_pc(name="Survivor", present=True, user_id=str(uuid.uuid4()))
        survivor.campaign_id = campaign_id

        active_state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(
                pbp_enabled=True,
                turn_order=[str(user_id), str(survivor.document["player_binding"]["user_id"])],
                current_turn_player_id=str(user_id),
            ),
        )
        active_state.combat.initiative_order = [
            InitiativeEntry(entity_id=str(pc.id), entity_type="PC", display_name="Removed"),
            InitiativeEntry(entity_id=str(survivor.id), entity_type="PC", display_name="Survivor"),
        ]
        active_state.combat.current_turn_entity_id = str(pc.id)
        active_state.chat_buffer = [
            ChatMessage(
                id="msg-1",
                timestamp="2026-01-01T00:00:00Z",
                sender_id=str(user_id),
                type="SPEAK",
                text="History",
            )
        ]

        paused_state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign_id), status="PAUSED"),
            context=SceneContext(),
            turn_management=TurnManagement(turn_order=[str(user_id)]),
        )

        active_scene = _scene_with_state(campaign_id, active_state, status="ACTIVE")
        paused_scene = _scene_with_state(campaign_id, paused_state, status="PAUSED")

        db = AsyncMock()
        db.scalars = AsyncMock(
            return_value=MagicMock(all=lambda: [active_scene, paused_scene])
        )
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch(
            "app.services.scenes.sync_turn_management_from_initiative",
            new=AsyncMock(),
        ):
            changed = asyncio.run(
                remove_player_from_open_scenes(
                    db,
                    campaign_id,
                    user_id,
                    pc=pc,
                )
            )

        assert changed == [active_scene, paused_scene]
        active_loaded = load_scene_state(active_scene)
        paused_loaded = load_scene_state(paused_scene)
        assert str(user_id) not in active_loaded.turn_management.turn_order
        assert str(pc.id) not in [entry.entity_id for entry in active_loaded.combat.initiative_order]
        assert active_loaded.combat.current_turn_entity_id == str(survivor.id)
        assert active_loaded.chat_buffer[0].text == "History"
        assert str(user_id) not in paused_loaded.turn_management.turn_order
        assert pc.document["player_binding"]["is_active_in_campaign"] is False
        assert pc.document["state_flags"]["is_present_in_scene"] is False
        db.commit.assert_awaited_once()


class TestRemoveCampaignMember:
    def test_removes_member_and_broadcasts_scene_updates(self):
        campaign_id = uuid.uuid4()
        user_id = uuid.uuid4()
        membership = CampaignMember(
            campaign_id=campaign_id,
            user_id=user_id,
            role="PLAYER",
        )
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
        db.scalar = AsyncMock(return_value=membership)
        db.delete = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with (
            patch(
                "app.services.entities.find_pc_by_user",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.scenes.remove_player_from_open_scenes",
                new=AsyncMock(return_value=[scene]),
            ) as cleanup,
            patch(
                "app.services.scene_ws.broadcast_scene_update",
                new=AsyncMock(),
            ) as broadcast_scene,
            patch(
                "app.services.campaign_ws.campaign_ws_manager.broadcast_presence",
                new=AsyncMock(),
            ) as broadcast_presence,
        ):
            asyncio.run(remove_campaign_member(db, campaign_id, user_id))

        cleanup.assert_awaited_once_with(
            db,
            campaign_id,
            user_id,
            pc=None,
            commit=False,
        )
        db.delete.assert_awaited_once_with(membership)
        db.commit.assert_awaited_once()
        broadcast_scene.assert_awaited_once()
        broadcast_presence.assert_awaited_once_with(str(campaign_id))

    def test_rejects_removing_only_master(self):
        campaign_id = uuid.uuid4()
        user_id = uuid.uuid4()
        membership = CampaignMember(
            campaign_id=campaign_id,
            user_id=user_id,
            role="MASTER",
        )

        db = AsyncMock()
        db.scalar = AsyncMock(side_effect=[membership, 1])
        db.delete = AsyncMock()

        with pytest.raises(CampaignServiceError, match="only master"):
            asyncio.run(remove_campaign_member(db, campaign_id, user_id))

        db.delete.assert_not_called()

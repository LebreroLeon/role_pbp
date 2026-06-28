import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import CampaignEntity, Scene
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.scene import (
    InitiativeEntry,
    PostMessageRequest,
    SceneContext,
    SceneMetadata,
    SceneState,
    SceneTurnManagementUpdate,
    TurnManagement,
)
from app.services.pbp_turn import (
    PbpTurnError,
    advance_pbp_turn,
    assert_pbp_advance_allowed,
    assert_pbp_post_allowed,
    build_default_pbp_order,
    ensure_pbp_initiative_order,
    is_pbp_enforcement_active,
    sort_initiative_entries,
)
from app.services.scenes import (
    SceneServiceError,
    advance_scene_pbp_turn,
    post_message,
    update_scene_turn_management,
)


def _pbp_state(*, pbp_enabled: bool = True, turn_order: list[str] | None = None) -> SceneState:
    order = turn_order or ["player-a", "player-b"]
    return SceneState(
        metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
        context=SceneContext(),
        turn_management=TurnManagement(
            pbp_enabled=pbp_enabled,
            turn_order=order,
            current_turn_player_id=order[0],
            order_source="manual",
        ),
    )


def _make_pc(*, name: str, present: bool = True, user_id: str) -> CampaignEntity:
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
            "identity": {"name": name, "concept": "Guard", "faction_id": "x", "current_location_id": "y"},
            "state_flags": {"is_present_in_scene": False},
        },
    )


class TestPbpTurnHelpers:
    def test_is_pbp_enforcement_active(self):
        assert is_pbp_enforcement_active(_pbp_state(pbp_enabled=True))
        assert not is_pbp_enforcement_active(_pbp_state(pbp_enabled=False))

    def test_advance_pbp_turn_cycles_players(self):
        state = _pbp_state()
        advance_pbp_turn(state)
        assert state.turn_management.current_turn_player_id == "player-b"
        advance_pbp_turn(state)
        assert state.turn_management.current_turn_player_id == "player-a"

    def test_advance_pbp_turn_cycles_entities(self):
        state = _pbp_state()
        state.combat.initiative_order = [
            InitiativeEntry(entity_id="pc-1", entity_type="PC", display_name="Norman"),
            InitiativeEntry(entity_id="npc-1", entity_type="NPC", display_name="Arturo"),
        ]
        state.combat.current_turn_entity_id = "pc-1"
        advance_pbp_turn(state)
        assert state.combat.current_turn_entity_id == "npc-1"
        advance_pbp_turn(state)
        assert state.combat.current_turn_entity_id == "pc-1"

    def test_sort_initiative_entries_by_score(self):
        entries = [
            InitiativeEntry(entity_id="a", initiative_score=10),
            InitiativeEntry(entity_id="b", initiative_score=18),
        ]
        sorted_entries = sort_initiative_entries(entries, {}, "initiative")
        assert [entry.entity_id for entry in sorted_entries] == ["b", "a"]

    def test_build_default_pbp_order_includes_present_pcs_and_active_npcs(self):
        norman = _make_pc(name="Norman", present=True, user_id="player-1")
        arturo_npc = _make_npc(name="Arturo")
        off_scene = _make_pc(name="Away", present=False, user_id="player-2")

        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[str(arturo_npc.id)]),
        )

        entries = build_default_pbp_order(state, [norman, arturo_npc, off_scene])
        names = [entry.display_name for entry in entries]
        entity_ids = [entry.entity_id for entry in entries]

        assert names == ["Norman", "Arturo"]
        assert str(norman.id) in entity_ids
        assert str(arturo_npc.id) in entity_ids
        assert str(off_scene.id) not in entity_ids


def test_assert_pbp_post_allowed_blocks_wrong_player():
    state = _pbp_state()
    db = AsyncMock()

    async def run_test():
        with pytest.raises(PbpTurnError, match="No es tu turno"):
            await assert_pbp_post_allowed(
                db,
                uuid.uuid4(),
                state,
                "player-b",
                "PLAYER",
            )

    asyncio.run(run_test())


def test_assert_pbp_post_allowed_master_bypass():
    state = _pbp_state()
    db = AsyncMock()
    asyncio.run(assert_pbp_post_allowed(db, uuid.uuid4(), state, "master-id", "MASTER"))


def test_assert_pbp_advance_allowed_blocks_wrong_player():
    state = _pbp_state()
    db = AsyncMock()

    async def run_test():
        with pytest.raises(PbpTurnError, match="Solo quien tiene el turno"):
            await assert_pbp_advance_allowed(
                db,
                uuid.uuid4(),
                state,
                "player-b",
                "PLAYER",
            )

    asyncio.run(run_test())


def test_assert_pbp_advance_allowed_current_player():
    state = _pbp_state()
    db = AsyncMock()
    asyncio.run(assert_pbp_advance_allowed(db, uuid.uuid4(), state, "player-a", "PLAYER"))


def test_assert_pbp_advance_allowed_master_bypass():
    state = _pbp_state()
    db = AsyncMock()
    asyncio.run(assert_pbp_advance_allowed(db, uuid.uuid4(), state, "master-id", "MASTER"))


def test_ensure_pbp_initiative_order_populates_from_scene_entities():
    campaign_id = uuid.uuid4()
    norman = _make_pc(name="Norman", present=True, user_id="player-1")
    norman.campaign_id = campaign_id
    arturo = _make_npc(name="Arturo")
    arturo.campaign_id = campaign_id

    state = SceneState(
        metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
        context=SceneContext(active_npc_ids=[str(arturo.id)]),
        turn_management=TurnManagement(
            pbp_enabled=True,
            turn_order=["master-only"],
            current_turn_player_id="master-only",
        ),
    )

    db = AsyncMock()
    db.scalars = AsyncMock(
        side_effect=[
            MagicMock(all=lambda: [norman]),
            MagicMock(all=lambda: [arturo]),
            MagicMock(first=lambda: norman),
        ]
    )
    db.scalar = AsyncMock(return_value=norman)

    async def run_test():
        populated = await ensure_pbp_initiative_order(db, campaign_id, state)
        assert populated is True
        assert len(state.combat.initiative_order) == 2
        assert state.combat.current_turn_entity_id == str(norman.id)
        assert state.turn_management.current_turn_player_id == "player-1"

    asyncio.run(run_test())


def test_update_scene_turn_management_enables_pbp_and_builds_order():
    campaign_id = uuid.uuid4()
    norman = _make_pc(name="Norman", present=True, user_id="player-1")
    norman.campaign_id = campaign_id
    arturo = _make_npc(name="Arturo")
    arturo.campaign_id = campaign_id

    scene = Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        status="ACTIVE",
        scene_state=_pbp_state(turn_order=["master-user"]).model_dump(),
    )
    scene.scene_state["turn_management"]["pbp_enabled"] = False
    scene.scene_state["context"] = {"active_npc_ids": [str(arturo.id)]}

    db = AsyncMock()
    db.scalars = AsyncMock(
        side_effect=[
            MagicMock(all=lambda: [norman]),
            MagicMock(all=lambda: [arturo]),
            MagicMock(first=lambda: norman),
        ]
    )
    db.scalar = AsyncMock(return_value=norman)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def run_test():
        response = await update_scene_turn_management(
            db,
            scene,
            SceneTurnManagementUpdate(pbp_enabled=True),
        )
        state = response.scene_state
        assert state.turn_management.pbp_enabled is True
        assert len(state.combat.initiative_order) == 2
        assert state.combat.initiative_order[0].display_name == "Norman"
        assert state.combat.initiative_order[1].display_name == "Arturo"

    asyncio.run(run_test())


def test_advance_scene_pbp_turn_advances_entity_order():
    campaign_id = uuid.uuid4()
    player_id = uuid.uuid4()
    norman = _make_pc(name="Norman", present=True, user_id=str(player_id))
    arturo = _make_npc(name="Arturo")

    state = SceneState(
        metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
        context=SceneContext(active_npc_ids=[str(arturo.id)]),
        turn_management=TurnManagement(pbp_enabled=True, turn_order=[]),
    )
    state.combat.initiative_order = [
        InitiativeEntry(entity_id=str(norman.id), entity_type="PC", display_name="Norman"),
        InitiativeEntry(entity_id=str(arturo.id), entity_type="NPC", display_name="Arturo"),
    ]
    state.combat.current_turn_entity_id = str(norman.id)

    scene = Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        status="ACTIVE",
        scene_state=state.model_dump(),
    )

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=norman)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def run_test():
        with patch(
            "app.services.pbp_turn.find_pc_by_user",
            new_callable=AsyncMock,
            return_value=norman,
        ):
            response = await advance_scene_pbp_turn(
                db,
                scene,
                user_id=str(player_id),
                user_role="PLAYER",
            )
        assert response.scene_state.combat.current_turn_entity_id == str(arturo.id)

    asyncio.run(run_test())


def test_advance_scene_pbp_turn_rejects_wrong_player():
    campaign_id = uuid.uuid4()
    norman_user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    norman = _make_pc(name="Norman", present=True, user_id=str(norman_user_id))
    arturo = _make_npc(name="Arturo")

    state = SceneState(
        metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
        context=SceneContext(active_npc_ids=[str(arturo.id)]),
        turn_management=TurnManagement(pbp_enabled=True, turn_order=[]),
    )
    state.combat.initiative_order = [
        InitiativeEntry(entity_id=str(norman.id), entity_type="PC", display_name="Norman"),
        InitiativeEntry(entity_id=str(arturo.id), entity_type="NPC", display_name="Arturo"),
    ]
    state.combat.current_turn_entity_id = str(norman.id)

    scene = Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        status="ACTIVE",
        scene_state=state.model_dump(),
    )

    db = AsyncMock()
    other_pc = _make_pc(name="Other", present=True, user_id=str(other_user_id))

    async def run_test():
        with patch(
            "app.services.pbp_turn.find_pc_by_user",
            new_callable=AsyncMock,
            return_value=other_pc,
        ):
            with pytest.raises(SceneServiceError, match="Solo quien tiene el turno"):
                await advance_scene_pbp_turn(
                    db,
                    scene,
                    user_id=str(other_user_id),
                    user_role="PLAYER",
                )

    asyncio.run(run_test())


@pytest.mark.asyncio
async def test_post_message_does_not_auto_advance_turn():
    campaign_id = uuid.uuid4()
    player_id = "player-a"
    state = _pbp_state(turn_order=[player_id, "player-b"])
    scene = Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        status="ACTIVE",
        scene_state=state.model_dump(),
    )

    with (
        patch("app.services.scenes.load_scene_state", return_value=state),
        patch("app.services.scenes.save_scene_state"),
        patch("app.services.scenes.ensure_scene_post_allowed"),
        patch("app.services.scenes.assert_pbp_post_allowed", new_callable=AsyncMock),
        patch(
            "app.services.scenes.resolve_message_speaker_fields",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch("app.services.scenes.append_chat_message", new_callable=AsyncMock),
        patch("app.services.scenes.rag_service.index_message", new_callable=AsyncMock),
        patch("app.services.scenes.advance_pbp_turn") as advance_mock,
    ):
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        await post_message(
            db,
            scene,
            player_id,
            PostMessageRequest(type="SPEAK", text="Hola a todos."),
            sender_role="PLAYER",
        )

        advance_mock.assert_not_called()
        assert state.turn_management.current_turn_player_id == player_id


def test_update_scene_turn_management_assigns_turn_to_entity():
    campaign_id = uuid.uuid4()
    norman = _make_pc(name="Norman", present=True, user_id="player-1")
    arturo = _make_npc(name="Arturo")

    state = SceneState(
        metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
        turn_management=TurnManagement(pbp_enabled=True),
    )
    state.combat.initiative_order = [
        InitiativeEntry(entity_id=str(norman.id), entity_type="PC", display_name="Norman"),
        InitiativeEntry(entity_id=str(arturo.id), entity_type="NPC", display_name="Arturo"),
    ]
    state.combat.current_turn_entity_id = str(norman.id)

    scene = Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        status="ACTIVE",
        scene_state=state.model_dump(),
    )

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=None)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def run_test():
        response = await update_scene_turn_management(
            db,
            scene,
            SceneTurnManagementUpdate(current_turn_entity_id=str(arturo.id)),
        )
        assert response.scene_state.combat.current_turn_entity_id == str(arturo.id)
        assert response.scene_state.turn_management.current_turn_player_id is None

    asyncio.run(run_test())

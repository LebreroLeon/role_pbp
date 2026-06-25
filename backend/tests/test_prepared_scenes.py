import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import pytest

from app.models.campaign import Campaign, CampaignEntity, Scene
from app.schemas.scene import (
    PreparedEntityRef,
    SceneContext,
    SceneCreate,
    SceneMetadata,
    ScenePrepUpdate,
    SceneState,
    TurnManagement,
)
from app.services.scenes import (
    SceneServiceError,
    activate_scene,
    close_scene,
    create_scene,
    get_master_briefing,
    update_scene_prep,
)


def _make_scene(*, status: str = "PREPARED", scene_number: int | None = 1, campaign_id: uuid.UUID | None = None) -> Scene:
    cid = campaign_id or uuid.uuid4()
    return Scene(
        id=uuid.uuid4(),
        campaign_id=cid,
        scene_number=scene_number,
        display_name="Puerta A",
        status=status,
        scene_state={
            "metadata": {"campaign_id": str(cid), "status": status},
            "context": {
                "location_id": None,
                "active_npc_ids": [],
                "hidden_npc_ids": [],
                "scene_objective": "Explorar el pasillo",
                "master_prep_notes": "Trampa en el suelo",
                "opening_narration": "Un pasillo oscuro se abre ante vosotros.",
                "prepared_entity_refs": [],
            },
            "turn_management": {"current_turn_player_id": None, "turn_order": []},
            "memory_settings": {
                "max_chat_buffer_size": 20,
                "rag_top_k_matches": 3,
                "max_player_lore_queries_per_scene": 3,
            },
            "chat_buffer": [],
            "state_flags": {
                "conflict_mode_active": False,
                "ai_alert_triggered": False,
                "remaining_player_lore_tokens": 3,
            },
            "combat": {
                "is_active": False,
                "round": 0,
                "initiative_order": [],
                "current_turn_entity_id": None,
                "conflict_mode_active": False,
            },
        },
    )


def _npc_entity(campaign_id: uuid.UUID, name: str = "Goblin") -> CampaignEntity:
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        entity_type="NPC",
        document={
            "identity": {"name": name, "concept": "Enemigo"},
            "ai_narrative_profile": {
                "public_description": "Un goblin",
                "secret_lore_master": "Sirve al jefe orco",
                "personality_traits": [],
                "voice_and_tone": "Gruñón",
            },
            "state_flags": {
                "is_dead": False,
                "is_present_in_scene": False,
                "attitude_towards_party": "hostile",
                "has_met_party": False,
                "player_visibility": "visible",
                "hidden_from_players": False,
            },
        },
    )


def _pc_entity(campaign_id: uuid.UUID, name: str = "Kaelen") -> CampaignEntity:
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        entity_type="PC",
        document={
            "identity": {"name": name},
            "player_binding": {"user_id": str(uuid.uuid4())},
            "state_flags": {"is_present_in_scene": False, "is_incapacitated": False},
        },
    )


class TestPreparedSceneCrud:
    def test_create_prepared_scene_does_not_pause_active(self):
        campaign_id = uuid.uuid4()
        existing = _make_scene(status="ACTIVE", scene_number=1, campaign_id=campaign_id)
        creator_id = uuid.uuid4()

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=Campaign(id=campaign_id, name="Test"))
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        response = asyncio.run(
            create_scene(
                db,
                campaign_id,
                SceneCreate(
                    campaign_id=str(campaign_id),
                    display_name="Puerta B",
                    scene_objective="Otra ruta",
                    status="PREPARED",
                ),
                creator_id,
            )
        )

        assert existing.status == "ACTIVE"
        assert response.status == "PREPARED"
        assert response.scene_number is None
        db.add.assert_called_once()

    def test_update_scene_prep_persists_fields(self):
        scene = _make_scene()
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        npc_id = str(uuid.uuid4())
        response = asyncio.run(
            update_scene_prep(
                db,
                scene,
                ScenePrepUpdate(
                    scene_objective="Nuevo objetivo",
                    master_prep_notes="Notas del máster",
                    prepared_entity_refs=[
                        PreparedEntityRef(
                            entity_id=npc_id,
                            player_visibility="unknown",
                            add_to_roster=True,
                        )
                    ],
                ),
            )
        )

        assert scene.scene_state["context"]["scene_objective"] == "Nuevo objetivo"
        assert scene.scene_state["context"]["master_prep_notes"] == "Notas del máster"
        assert response.scene_state.context.prepared_entity_refs[0].entity_id == npc_id

    def test_update_scene_prep_forces_pc_visibility_visible(self):
        campaign_id = uuid.uuid4()
        scene = _make_scene(campaign_id=campaign_id)
        pc = _pc_entity(campaign_id)
        pc_id = str(pc.id)

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[pc])))
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        response = asyncio.run(
            update_scene_prep(
                db,
                scene,
                ScenePrepUpdate(
                    prepared_entity_refs=[
                        PreparedEntityRef(
                            entity_id=pc_id,
                            player_visibility="hidden",
                            add_to_roster=True,
                        )
                    ],
                ),
            )
        )

        saved = response.scene_state.context.prepared_entity_refs[0]
        assert saved.entity_id == pc_id
        assert saved.player_visibility == "visible"


class TestActivatePreparedScene:
    def test_activate_applies_entity_refs_to_roster(self):
        campaign_id = uuid.uuid4()
        scene = _make_scene(campaign_id=campaign_id)
        npc = _npc_entity(campaign_id)
        npc_id = str(npc.id)
        scene.scene_state["context"]["prepared_entity_refs"] = [
            {
                "entity_id": npc_id,
                "player_visibility": "unknown",
                "add_to_roster": True,
            }
        ]

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.scalars = AsyncMock(
            side_effect=[
                MagicMock(all=MagicMock(return_value=[])),
                MagicMock(all=MagicMock(return_value=[npc])),
                MagicMock(all=MagicMock(return_value=[npc])),
                MagicMock(all=MagicMock(return_value=[])),
            ]
        )
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch("app.services.scenes.mark_all_campaign_pcs_present_for_scene", new=AsyncMock()):
            response = asyncio.run(activate_scene(db, scene, activator_user_id=str(uuid.uuid4())))

        assert scene.status == "ACTIVE"
        assert npc_id in response.scene_state.context.active_npc_ids
        assert npc_id in response.scene_state.context.hidden_npc_ids
        assert npc.document["state_flags"]["player_visibility"] == "unknown"

    def test_activate_pc_ignores_hidden_visibility_on_ref(self):
        campaign_id = uuid.uuid4()
        scene = _make_scene(campaign_id=campaign_id)
        pc = _pc_entity(campaign_id)
        pc_id = str(pc.id)
        scene.scene_state["context"]["prepared_entity_refs"] = [
            {
                "entity_id": pc_id,
                "player_visibility": "hidden",
                "add_to_roster": True,
            }
        ]

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.scalars = AsyncMock(
            side_effect=[
                MagicMock(all=MagicMock(return_value=[])),
                MagicMock(all=MagicMock(return_value=[pc])),
                MagicMock(all=MagicMock(return_value=[pc])),
                MagicMock(all=MagicMock(return_value=[])),
            ]
        )
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch("app.services.scenes.mark_all_campaign_pcs_present_for_scene", new=AsyncMock()), patch(
            "app.services.entities.set_pc_present_in_scene",
            new=AsyncMock(),
        ) as set_pc_present:
            asyncio.run(activate_scene(db, scene, activator_user_id=str(uuid.uuid4())))

        set_pc_present.assert_awaited_once()
        assert pc_id not in scene.scene_state["context"].get("hidden_npc_ids", [])
        assert pc_id not in scene.scene_state["context"].get("active_npc_ids", [])


class TestMasterBriefing:
    def test_get_master_briefing_includes_npc_secrets(self):
        campaign_id = uuid.uuid4()
        scene = _make_scene(campaign_id=campaign_id)
        npc = _npc_entity(campaign_id)
        npc_id = str(npc.id)
        scene.scene_state["context"]["prepared_entity_refs"] = [
            {"entity_id": npc_id, "player_visibility": "visible", "add_to_roster": True}
        ]

        closed = _make_scene(status="CLOSED", scene_number=1, campaign_id=campaign_id)
        closed.scene_state["metadata"]["closure_summary"] = "Resumen anterior"

        db = AsyncMock()
        db.scalar = AsyncMock(side_effect=[1, None, closed, None])
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[npc])))

        briefing = asyncio.run(get_master_briefing(db, scene))

        assert briefing.scene_objective == "Explorar el pasillo"
        assert briefing.next_scene_number == 2
        assert briefing.last_scene_summary == "Resumen anterior"
        assert len(briefing.npcs) == 1
        assert briefing.npcs[0].secret_lore_master == "Sirve al jefe orco"
        assert briefing.npcs[0].voice_and_tone == "Gruñón"


class TestActivateSceneNumbering:
    def test_activate_assigns_next_sequential_scene_number(self):
        campaign_id = uuid.uuid4()
        scene = _make_scene(status="PREPARED", scene_number=None, campaign_id=campaign_id)
        scene.scene_number = None

        db = AsyncMock()
        db.scalar = AsyncMock(side_effect=[None, 1])
        db.scalars = AsyncMock(
            side_effect=[
                MagicMock(all=MagicMock(return_value=[])),
                MagicMock(all=MagicMock(return_value=[])),
                MagicMock(all=MagicMock(return_value=[])),
            ]
        )
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch("app.services.scenes.mark_all_campaign_pcs_present_for_scene", new=AsyncMock()):
            response = asyncio.run(activate_scene(db, scene, activator_user_id=str(uuid.uuid4())))

        assert scene.scene_number == 2
        assert response.scene_number == 2
        assert scene.status == "ACTIVE"


class TestCloseScenePicker:
    def test_close_scene_returns_prepared_scenes(self):
        campaign_id = uuid.uuid4()
        scene = _make_scene(status="ACTIVE", campaign_id=campaign_id)
        prepared = _make_scene(status="PREPARED", scene_number=None, campaign_id=campaign_id)
        prepared.display_name = "Puerta B"

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[prepared])))

        with patch(
            "app.services.scenes.generate_scene_closure_summary",
            new=AsyncMock(return_value="Resumen."),
        ), patch("app.services.scenes.rag_service.index_message", new=AsyncMock()), patch(
            "app.services.scenes.rag_service.purge_semantic_cache",
            new=AsyncMock(),
        ):
            result = asyncio.run(close_scene(db, scene))

        assert result.closed_scene.status == "CLOSED"
        assert len(result.prepared_scenes) == 1
        assert result.prepared_scenes[0].display_name == "Puerta B"
        assert result.prepared_scenes[0].status == "PREPARED"

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import pytest

from app.models.campaign import Campaign, Scene
from app.schemas.scene import ChatMessage, SceneContext, SceneCreate, SceneMetadata, SceneState, TurnManagement
from app.services.scenes import (
    _build_narrative_text,
    _placeholder_scene_summary,
    SceneServiceError,
    close_scene,
    create_scene,
    delete_scene_message,
    generate_scene_closure_summary,
    pause_other_active_scenes,
    scene_to_response,
    start_active_scene,
    update_scene_display_name,
    update_scene_status,
)


def _make_scene(*, status: str = "ACTIVE", scene_number: int = 1, display_name: str | None = None) -> Scene:
    campaign_id = uuid.uuid4()
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=scene_number,
        display_name=display_name,
        status=status,
        scene_state={
            "metadata": {"campaign_id": str(campaign_id), "status": status},
            "context": {"location_id": None, "active_npc_ids": [], "hidden_npc_ids": [], "scene_objective": None},
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


class TestSceneLabelsAndSummary:
    def test_build_narrative_text_skips_dice_rolls(self):
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(),
            chat_buffer=[
                ChatMessage(
                    timestamp="t1",
                    sender_id="u1",
                    type="ACTION",
                    text="Entran en la taberna.",
                ),
                ChatMessage(
                    timestamp="t2",
                    sender_id="u1",
                    type="DICE_ROLL",
                    text="Roll: 1d20 => 15",
                ),
            ],
        )
        assert _build_narrative_text(state) == "Entran en la taberna."

    def test_scene_to_response_includes_number_name_and_closed_summary(self):
        scene = _make_scene(status="CLOSED", scene_number=2, display_name="La taberna del Grifo")
        scene.scene_state["metadata"]["closure_summary"] = "Los héroes negocian con el tabernero."
        scene.scene_state["metadata"]["status"] = "CLOSED"

        response = scene_to_response(scene)
        assert response.scene_number == 2
        assert response.display_name == "La taberna del Grifo"
        assert response.summary == "Los héroes negocian con el tabernero."

    def test_generate_scene_closure_summary_without_llm(self):
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(),
            chat_buffer=[
                ChatMessage(
                    timestamp="t1",
                    sender_id="u1",
                    type="SPEAK",
                    text="Buenas noches.",
                )
            ],
        )
        summary = asyncio.run(
            generate_scene_closure_summary(
                state,
                scene_number=1,
                display_name="Posada",
            )
        )
        assert "Escena 1: Posada" in summary
        assert "Buenas noches." in summary

    def test_placeholder_summary_for_empty_chat(self):
        summary = _placeholder_scene_summary("", scene_number=3, display_name=None)
        assert summary == "Escena 3 — cerrada sin mensajes narrativos registrados."


class TestCloseScene:
    def test_close_scene_marks_closed_and_stores_summary(self):
        scene = _make_scene(display_name="Ruinas")
        scene.scene_state["chat_buffer"] = [
            {
                "id": "m1",
                "timestamp": "t1",
                "sender_id": "u1",
                "type": "ACTION",
                "text": "Exploran las ruinas.",
                "read_by": ["u1"],
            }
        ]
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch(
            "app.services.scenes.generate_scene_closure_summary",
            new=AsyncMock(return_value="Resumen de prueba."),
        ), patch("app.services.scenes.rag_service.index_message", new=AsyncMock()) as index_mock:
            response = asyncio.run(close_scene(db, scene))

        assert scene.status == "CLOSED"
        assert scene.scene_state["metadata"]["closure_summary"] == "Resumen de prueba."
        assert response.summary == "Resumen de prueba."
        index_mock.assert_awaited_once()

    def test_update_scene_display_name(self):
        scene = _make_scene()
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        response = asyncio.run(update_scene_display_name(db, scene, "  El muelle  "))
        assert scene.display_name == "El muelle"
        assert response.display_name == "El muelle"


class TestDeleteSceneMessage:
    def test_delete_scene_message_removes_from_buffer(self):
        scene = _make_scene()
        scene.scene_state["chat_buffer"] = [
            {
                "id": "keep-me",
                "timestamp": "t1",
                "sender_id": "u1",
                "type": "ACTION",
                "text": "Se queda.",
                "read_by": ["u1"],
            },
            {
                "id": "remove-me",
                "timestamp": "t2",
                "sender_id": "u1",
                "type": "ACTION",
                "text": "Se borra.",
                "read_by": ["u1"],
            },
        ]
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        response = asyncio.run(delete_scene_message(db, scene, "remove-me"))

        buffer_ids = [entry["id"] for entry in scene.scene_state["chat_buffer"]]
        assert buffer_ids == ["keep-me"]
        assert len(response.scene_state.chat_buffer) == 1

    def test_delete_scene_message_not_found(self):
        scene = _make_scene()
        db = AsyncMock()

        with pytest.raises(SceneServiceError, match="Message not found"):
            asyncio.run(delete_scene_message(db, scene, "missing"))

    def test_delete_scene_message_closed_scene(self):
        scene = _make_scene(status="CLOSED")
        db = AsyncMock()

        with pytest.raises(SceneServiceError, match="closed scene"):
            asyncio.run(delete_scene_message(db, scene, "any"))


class TestCloseSceneCombatPause:
    def test_close_scene_pauses_active_combat(self):
        scene = _make_scene()
        scene.scene_state["chat_buffer"] = [
            {
                "id": "m1",
                "timestamp": "t1",
                "sender_id": "u1",
                "type": "ACTION",
                "text": "Combate.",
                "read_by": ["u1"],
            }
        ]
        scene.scene_state["combat"]["is_active"] = True
        scene.scene_state["combat"]["conflict_mode_active"] = True
        scene.scene_state["state_flags"]["conflict_mode_active"] = True
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch(
            "app.services.scenes.generate_scene_closure_summary",
            new=AsyncMock(return_value="Fin del combate."),
        ), patch("app.services.scenes.rag_service.index_message", new=AsyncMock()):
            asyncio.run(close_scene(db, scene))

        assert scene.scene_state["combat"]["is_active"] is False
        assert scene.scene_state["combat"]["conflict_mode_active"] is False
        assert scene.scene_state["state_flags"]["conflict_mode_active"] is False


class TestSingleActiveSceneRule:
    def test_pause_other_active_scenes_updates_status_and_state(self):
        campaign_id = uuid.uuid4()
        scene_a = _make_scene(status="ACTIVE", scene_number=1)
        scene_a.campaign_id = campaign_id
        scene_b = _make_scene(status="ACTIVE", scene_number=2)
        scene_b.campaign_id = campaign_id

        db = AsyncMock()
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[scene_a, scene_b])))
        db.commit = AsyncMock()

        paused = asyncio.run(pause_other_active_scenes(db, campaign_id))
        assert paused == [scene_a, scene_b]
        assert scene_a.status == "PAUSED"
        assert scene_b.status == "PAUSED"
        assert scene_a.scene_state["metadata"]["status"] == "PAUSED"
        assert scene_b.scene_state["metadata"]["status"] == "PAUSED"

    def test_create_scene_pauses_existing_active_before_creating_new(self):
        campaign_id = uuid.uuid4()
        existing = _make_scene(status="ACTIVE", scene_number=1)
        existing.campaign_id = campaign_id
        creator_id = uuid.uuid4()

        db = AsyncMock()
        db.scalar = AsyncMock(
            side_effect=[
                Campaign(id=campaign_id, name="Test"),
                0,
            ]
        )
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[existing])))
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch(
            "app.services.scenes.mark_all_campaign_pcs_present_for_scene",
            new=AsyncMock(),
        ):
            response = asyncio.run(
                create_scene(
                    db,
                    campaign_id,
                    SceneCreate(campaign_id=str(campaign_id), display_name="Nueva"),
                    creator_id,
                )
            )

        assert existing.status == "PAUSED"
        assert response.status == "ACTIVE"
        assert response.scene_number == 1
        db.add.assert_called_once()

    def test_update_scene_status_to_active_pauses_other_scenes(self):
        campaign_id = uuid.uuid4()
        current = _make_scene(status="PAUSED", scene_number=1)
        current.campaign_id = campaign_id
        other = _make_scene(status="ACTIVE", scene_number=2)
        other.campaign_id = campaign_id

        db = AsyncMock()
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[other])))
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch(
            "app.services.scenes.mark_all_campaign_pcs_present_for_scene",
            new=AsyncMock(),
        ):
            response = asyncio.run(update_scene_status(db, current, "ACTIVE"))
        assert other.status == "PAUSED"
        assert current.status == "ACTIVE"
        assert response.status == "ACTIVE"

    def test_start_active_scene_rejects_closed(self):
        scene = _make_scene(status="CLOSED", scene_number=1)
        db = AsyncMock()

        with pytest.raises(SceneServiceError, match="closed"):
            asyncio.run(start_active_scene(db, scene))

    def test_start_active_scene_pauses_current_active(self):
        campaign_id = uuid.uuid4()
        paused = _make_scene(status="PAUSED", scene_number=1)
        paused.campaign_id = campaign_id
        active = _make_scene(status="ACTIVE", scene_number=2)
        active.campaign_id = campaign_id

        db = AsyncMock()
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[active])))
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch(
            "app.services.scenes.mark_all_campaign_pcs_present_for_scene",
            new=AsyncMock(),
        ):
            response = asyncio.run(start_active_scene(db, paused))
        assert active.status == "PAUSED"
        assert paused.status == "ACTIVE"
        assert response.status == "ACTIVE"

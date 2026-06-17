import uuid
from unittest.mock import AsyncMock, patch
import asyncio

from app.models.campaign import Scene
from app.schemas.scene import ChatMessage, SceneContext, SceneMetadata, SceneState, TurnManagement
from app.services.scenes import (
    _build_narrative_text,
    _placeholder_scene_summary,
    close_scene,
    generate_scene_closure_summary,
    scene_to_response,
    update_scene_display_name,
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

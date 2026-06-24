import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import Scene
from app.schemas.scene import PostMessageRequest
from app.services.scenes import (
    SceneServiceError,
    ensure_scene_post_allowed,
    post_message,
)


def _make_scene(*, status: str = "PAUSED") -> Scene:
    campaign_id = uuid.uuid4()
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
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


class TestEnsureScenePostAllowed:
    def test_active_allows_player(self):
        ensure_scene_post_allowed(_make_scene(status="ACTIVE"), sender_role="PLAYER")

    def test_paused_blocks_player(self):
        with pytest.raises(SceneServiceError, match="congelada"):
            ensure_scene_post_allowed(_make_scene(status="PAUSED"), sender_role="PLAYER")

    def test_paused_allows_master(self):
        ensure_scene_post_allowed(_make_scene(status="PAUSED"), sender_role="MASTER")

    def test_closed_blocks_master(self):
        with pytest.raises(SceneServiceError, match="CLOSED"):
            ensure_scene_post_allowed(_make_scene(status="CLOSED"), sender_role="MASTER")


class TestPostMessageWhileFrozen:
    def test_player_message_rejected_when_paused(self):
        scene = _make_scene(status="PAUSED")
        db = AsyncMock()

        with pytest.raises(SceneServiceError, match="congelada"):
            asyncio.run(
                post_message(
                    db,
                    scene,
                    str(uuid.uuid4()),
                    PostMessageRequest(type="ACTION", text="Intento actuar."),
                    sender_role="PLAYER",
                )
            )

    def test_master_message_allowed_when_paused(self):
        scene = _make_scene(status="PAUSED")
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch("app.services.scenes.rag_service.index_message", new_callable=AsyncMock):
            response = asyncio.run(
                post_message(
                    db,
                    scene,
                    str(uuid.uuid4()),
                    PostMessageRequest(type="MASTER", text="La escena se detiene un instante."),
                    sender_role="MASTER",
                )
            )

        assert response.status == "PAUSED"
        assert len(scene.scene_state["chat_buffer"]) == 1
        assert scene.scene_state["chat_buffer"][0]["text"] == "La escena se detiene un instante."

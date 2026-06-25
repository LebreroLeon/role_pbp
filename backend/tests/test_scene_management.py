import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import Scene
from app.schemas.scene import SceneCreate
from app.services.scenes import (
    SceneServiceError,
    activate_scene,
    create_scene,
    delete_scene,
    require_no_other_open_scene,
)


def _make_scene(
    *,
    status: str = "PREPARED",
    scene_number: int | None = 1,
    campaign_id: uuid.UUID | None = None,
    scene_id: uuid.UUID | None = None,
) -> Scene:
    cid = campaign_id or uuid.uuid4()
    return Scene(
        id=scene_id or uuid.uuid4(),
        campaign_id=cid,
        scene_number=scene_number,
        display_name="Escena de prueba",
        status=status,
        scene_state={
            "metadata": {"campaign_id": str(cid), "status": status, "closure_summary": "Resumen guardado"},
            "context": {
                "location_id": None,
                "active_npc_ids": [],
                "hidden_npc_ids": [],
                "scene_objective": "Objetivo",
                "prepared_entity_refs": [],
            },
            "turn_management": {"current_turn_player_id": None, "turn_order": []},
            "memory_settings": {
                "max_chat_buffer_size": 20,
                "rag_top_k_matches": 3,
                "max_player_lore_queries_per_scene": 3,
            },
            "chat_buffer": [
                {
                    "id": "msg-1",
                    "timestamp": "t1",
                    "sender_id": "u1",
                    "type": "ACTION",
                    "text": "Mensaje de prueba",
                    "read_by": ["u1"],
                }
            ],
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


class TestRequireNoOtherOpenScene:
    def test_allows_when_no_open_scene(self):
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        asyncio.run(require_no_other_open_scene(db, uuid.uuid4()))

    def test_allows_when_open_scene_is_same(self):
        campaign_id = uuid.uuid4()
        scene = _make_scene(status="PAUSED", campaign_id=campaign_id)
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=scene)
        asyncio.run(require_no_other_open_scene(db, campaign_id, except_scene_id=scene.id))

    def test_blocks_when_other_open_scene_exists(self):
        campaign_id = uuid.uuid4()
        open_scene = _make_scene(status="ACTIVE", campaign_id=campaign_id)
        target = _make_scene(status="PREPARED", campaign_id=campaign_id)
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=open_scene)

        with pytest.raises(SceneServiceError, match="escena abierta"):
            asyncio.run(require_no_other_open_scene(db, campaign_id, except_scene_id=target.id))


class TestActivateWithOpenScene:
    def test_activate_prepared_closes_other_open_scene(self):
        campaign_id = uuid.uuid4()
        paused = _make_scene(status="PAUSED", campaign_id=campaign_id, scene_number=1)
        prepared = _make_scene(status="PREPARED", scene_number=None, campaign_id=campaign_id)

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.scalars = AsyncMock(
            side_effect=[
                MagicMock(all=MagicMock(return_value=[paused])),
                MagicMock(all=MagicMock(return_value=[])),
                MagicMock(all=MagicMock(return_value=[])),
            ]
        )
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: obj)

        with patch("app.services.scenes.mark_all_campaign_pcs_present_for_scene", new=AsyncMock()):
            response = asyncio.run(activate_scene(db, prepared, activator_user_id=str(uuid.uuid4())))

        assert paused.status == "CLOSED"
        assert prepared.status == "ACTIVE"
        assert response.status == "ACTIVE"


class TestDeleteScene:
    def test_delete_removes_scene_and_messages(self):
        scene = _make_scene(status="CLOSED")
        db = AsyncMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        db.commit = AsyncMock()

        with patch("app.services.scenes.rag_service.purge_semantic_cache", new=AsyncMock()):
            asyncio.run(delete_scene(db, scene))

        db.delete.assert_called_once_with(scene)
        assert db.execute.await_count == 2

    def test_delete_allows_active_scene(self):
        scene = _make_scene(status="ACTIVE")
        db = AsyncMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        db.commit = AsyncMock()

        with patch("app.services.scenes.rag_service.purge_semantic_cache", new=AsyncMock()):
            asyncio.run(delete_scene(db, scene))

        db.delete.assert_called_once_with(scene)

    def test_delete_allows_paused_scene(self):
        scene = _make_scene(status="PAUSED")
        db = AsyncMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        db.commit = AsyncMock()

        with patch("app.services.scenes.rag_service.purge_semantic_cache", new=AsyncMock()):
            asyncio.run(delete_scene(db, scene))

        db.delete.assert_called_once_with(scene)


class TestCreateSceneWithOpenScene:
    def test_create_active_closes_existing_open_scene(self):
        campaign_id = uuid.uuid4()
        open_scene = _make_scene(status="PAUSED", campaign_id=campaign_id)
        campaign = MagicMock()
        db = AsyncMock()
        db.scalar = AsyncMock(side_effect=[campaign, 0])
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[open_scene])))
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
                    uuid.uuid4(),
                )
            )

        assert open_scene.status == "CLOSED"
        assert response.status == "ACTIVE"

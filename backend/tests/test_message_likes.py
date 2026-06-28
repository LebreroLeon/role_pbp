import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.campaign import Scene
from app.models.user import User
from app.services.scenes import toggle_scene_message_like


def _make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="player@example.com",
        password_hash="hash",
        display_name="Player One",
    )


def _make_scene_with_message(message_id: str) -> Scene:
    campaign_id = uuid.uuid4()
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        display_name="Test scene",
        status="ACTIVE",
        scene_state={
            "metadata": {"campaign_id": str(campaign_id), "status": "ACTIVE"},
            "context": {"location_id": None, "active_npc_ids": [], "hidden_npc_ids": [], "scene_objective": None},
            "turn_management": {"current_turn_player_id": None, "turn_order": []},
            "memory_settings": {
                "max_chat_buffer_size": 60,
                "rag_top_k_matches": 3,
                "max_player_lore_queries_per_scene": 3,
            },
            "chat_buffer": [
                {
                    "id": message_id,
                    "timestamp": "2026-01-01T12:00:00Z",
                    "sender_id": str(uuid.uuid4()),
                    "type": "ACTION",
                    "text": "Hola",
                    "read_by": [],
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


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def override_db(mock_db):
    from app.core.database import get_db

    async def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


def _override_user(user: User):
    from app.api.deps import get_current_user

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override


class TestToggleSceneMessageLikeService:
    @pytest.mark.asyncio
    async def test_toggle_like_is_idempotent_per_user(self):
        user = _make_user()
        message_id = str(uuid.uuid4())
        scene = _make_scene_with_message(message_id)
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch(
            "app.services.scenes.fetch_likes_by_message_id",
            new=AsyncMock(return_value={message_id: [str(user.id)]}),
        ):
            liked = await toggle_scene_message_like(db, scene, str(user.id), message_id)
            assert liked.scene_state.chat_buffer[0].like_count == 1
            assert str(user.id) in liked.scene_state.chat_buffer[0].liked_by_user_ids

        existing_like = MagicMock()
        db.scalar = AsyncMock(return_value=existing_like)
        db.delete = AsyncMock()

        with patch(
            "app.services.scenes.fetch_likes_by_message_id",
            new=AsyncMock(return_value={}),
        ):
            unliked = await toggle_scene_message_like(db, scene, str(user.id), message_id)
            assert unliked.scene_state.chat_buffer[0].like_count == 0
            assert unliked.scene_state.chat_buffer[0].liked_by_user_ids == []

        db.delete.assert_awaited_once_with(existing_like)


class TestToggleSceneMessageLikeRoute:
    @pytest.mark.asyncio
    async def test_post_like_broadcasts_scene_update(self, override_db):
        user = _make_user()
        _override_user(user)
        from app.services.scenes import apply_likes_to_scene_state, scene_to_response

        scene = _make_scene_with_message(str(uuid.uuid4()))
        message_id = scene.scene_state["chat_buffer"][0]["id"]
        enriched = scene_to_response(scene)
        apply_likes_to_scene_state(enriched.scene_state, {message_id: [str(user.id)]})

        with (
            patch("app.api.routes.scenes.get_scene_for_member", new=AsyncMock(return_value=scene)),
            patch("app.api.routes.scenes.require_player_open_scene", new=AsyncMock()),
            patch(
                "app.api.routes.scenes.toggle_scene_message_like",
                new=AsyncMock(return_value=enriched),
            ) as toggle_like,
            patch(
                "app.api.routes.scenes.broadcast_scene_update",
                new=AsyncMock(return_value=enriched),
            ) as broadcast,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/scenes/{scene.id}/messages/{message_id}/like",
                )

        assert response.status_code == 200
        toggle_like.assert_awaited_once()
        broadcast.assert_awaited_once()

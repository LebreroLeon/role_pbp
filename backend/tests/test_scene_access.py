import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.campaign import Scene
from app.models.user import User
from app.schemas.scene import SceneResponse


def _make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="user@test.com",
        password_hash="hash",
        display_name="Test User",
    )


def _make_closed_scene(campaign_id: uuid.UUID) -> Scene:
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        display_name="Closed scene",
        status="CLOSED",
        scene_state={
            "metadata": {"campaign_id": str(campaign_id), "status": "CLOSED"},
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


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def override_db(mock_db):
    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


def _override_user(user: User):
    async def _get_current_user():
        return user

    app.dependency_overrides[get_current_user] = _get_current_user


@pytest.mark.asyncio
async def test_player_cannot_create_scene(override_db, mock_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    _override_user(user)

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/scenes",
                json={"campaign_id": str(campaign_id)},
            )

    assert response.status_code == 403
    assert response.json()["detail"] == "Master role required"


@pytest.mark.asyncio
async def test_master_can_create_scene(override_db, mock_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    _override_user(user)

    scene_response = SceneResponse(
        id=str(scene_id),
        campaign_id=str(campaign_id),
        scene_number=1,
        display_name="New scene",
        status="ACTIVE",
        scene_state={
            "metadata": {"campaign_id": str(campaign_id), "status": "ACTIVE"},
            "context": {},
            "turn_management": {},
            "memory_settings": {},
            "chat_buffer": [],
            "state_flags": {},
            "combat": {},
        },
    )

    with (
        patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="MASTER"),
        patch("app.api.routes.scenes.create_scene", new_callable=AsyncMock, return_value=scene_response),
        patch("app.api.routes.scenes.scene_ws_manager.broadcast", new_callable=AsyncMock),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/scenes",
                json={"campaign_id": str(campaign_id), "display_name": "New scene"},
            )

    assert response.status_code == 201
    assert response.json()["id"] == str(scene_id)


@pytest.mark.asyncio
async def test_player_gets_403_on_chat_post_without_active_scene(override_db, mock_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    closed_scene = _make_closed_scene(campaign_id)
    _override_user(user)

    with (
        patch("app.api.deps.get_scene_by_id", new_callable=AsyncMock, return_value=closed_scene),
        patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/scenes/{closed_scene.id}/messages",
                json={"type": "ACTION", "text": "Hello"},
            )

    assert response.status_code == 403
    assert "No active scene" in response.json()["detail"]

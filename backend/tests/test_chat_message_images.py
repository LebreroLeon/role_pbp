"""Tests for scene chat message image uploads."""

import uuid
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.campaign import Scene
from app.models.user import User
from app.schemas.scene import PostMessageRequest
from app.services.chat_message_images import message_image_api_path, save_scene_message_image_file
from app.services.scenes import post_message


def _make_user(*, role: str = "MASTER") -> User:
    return User(
        id=uuid.uuid4(),
        email="master@test.com",
        password_hash="hash",
        display_name="Master",
    )


def _make_scene(campaign_id: uuid.UUID | None = None) -> Scene:
    cid = campaign_id or uuid.uuid4()
    return Scene(
        id=uuid.uuid4(),
        campaign_id=cid,
        scene_number=1,
        display_name="Test scene",
        status="ACTIVE",
        scene_state={
            "metadata": {"campaign_id": str(cid), "status": "ACTIVE"},
            "chat_buffer": [],
            "memory_settings": {"max_chat_buffer_size": 60},
        },
    )


@pytest.mark.asyncio
async def test_save_and_resolve_message_image(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))

    from importlib import reload
    import app.core.config as config_module
    import app.services.object_storage as storage_module

    reload(config_module)
    reload(storage_module)

    scene = _make_scene()
    image_url = save_scene_message_image_file(
        scene,
        original_name="map.png",
        content=b"\x89PNG fake",
        mime_type="image/png",
    )

    assert image_url.startswith(f"/api/v1/scenes/{scene.id}/message-images/")

    from app.services.chat_message_images import resolve_scene_message_image_storage

    resolved = resolve_scene_message_image_storage(scene, image_url)
    assert resolved is not None
    key, media_type = resolved
    assert media_type == "image/png"
    assert key.endswith(".png")


@pytest.mark.asyncio
async def test_post_message_with_image_master_only():
    scene = _make_scene()
    user = _make_user()
    image_id = uuid.uuid4()
    image_url = message_image_api_path(scene.id, image_id)

    with (
        patch("app.services.scenes.load_scene_state") as load_state,
        patch("app.services.scenes.save_scene_state"),
        patch("app.services.scenes.validate_message_image_url"),
        patch("app.services.scenes.ensure_scene_post_allowed"),
        patch("app.services.scenes.assert_pbp_post_allowed", new_callable=AsyncMock),
        patch("app.services.scenes.resolve_message_speaker_fields", new_callable=AsyncMock, return_value={}),
        patch("app.services.scenes.rag_service.index_message", new_callable=AsyncMock),
    ):
        from app.schemas.scene import SceneState

        state = SceneState.model_validate(scene.scene_state)
        load_state.return_value = state

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        await post_message(
            db,
            scene,
            str(user.id),
            PostMessageRequest(type="MASTER", text="Un mapa del calabozo.", image_url=image_url),
            sender_role="MASTER",
        )

        last_message = state.chat_buffer[-1]
        assert last_message.image_url == image_url
        assert last_message.text == "Un mapa del calabozo."


@pytest.mark.asyncio
async def test_post_message_image_rejected_for_player():
    scene = _make_scene()
    user = _make_user()
    image_url = message_image_api_path(scene.id, uuid.uuid4())

    with (
        patch("app.services.scenes.ensure_scene_post_allowed"),
        patch("app.services.scenes.assert_pbp_post_allowed", new_callable=AsyncMock),
        patch("app.services.scenes.load_scene_state") as load_state,
        patch("app.services.scenes.resolve_message_speaker_fields", new_callable=AsyncMock, return_value={}),
    ):
        from app.schemas.scene import SceneState
        from app.services.scenes import SceneServiceError

        state = SceneState.model_validate(scene.scene_state)
        load_state.return_value = state

        db = AsyncMock()
        with pytest.raises(SceneServiceError, match="Máster"):
            await post_message(
                db,
                scene,
                str(user.id),
                PostMessageRequest(type="ACTION", text="Mira esto.", image_url=image_url),
                sender_role="PLAYER",
            )

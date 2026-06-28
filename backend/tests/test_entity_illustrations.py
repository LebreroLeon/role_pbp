"""Tests for entity illustration upload and player visibility."""

import uuid
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.campaign import CampaignEntity
from app.models.user import User
from app.services.entities import mask_hidden_npc_document
from app.services.entity_illustrations import (
    player_can_view_entity_illustration,
    read_entity_illustration_url,
    write_entity_illustration_url,
)


def _make_user(*, user_id: uuid.UUID | None = None) -> User:
    return User(
        id=user_id or uuid.uuid4(),
        email="master@test.com",
        password_hash="hash",
        display_name="Master",
    )


def _pc_document(*, user_id: uuid.UUID | None = None) -> dict:
    uid = user_id or uuid.uuid4()
    return {
        "metadata": {"type": "PC", "system_agnostic": True, "version": "2.0.0"},
        "identity": {"name": "Aldric", "concept": "Fighter"},
        "player_binding": {"user_id": str(uid), "is_active_in_campaign": True},
        "public_profile": {
            "description": "A brave warrior",
            "personality_traits": [],
        },
        "system_mechanics": {"system_name": "agnóstico", "stats_summary": {}},
        "state_flags": {"is_present_in_scene": False, "is_incapacitated": False},
    }


def _npc_document(*, visibility: str = "visible") -> dict:
    hidden = visibility == "hidden"
    return {
        "metadata": {"type": "NPC", "system_agnostic": True, "version": "2.0.0"},
        "identity": {"name": "Arturo", "concept": "Spy"},
        "ai_narrative_profile": {
            "public_description": "Shady",
            "secret_lore_master": "Secret",
            "personality_traits": ["quiet"],
            "voice_and_tone": "whisper",
            "illustration_url": "/api/v1/entities/test/illustration",
        },
        "system_mechanics": {
            "system_name": "agnóstico",
            "power_scale": "medium",
            "stats_summary": {},
            "notable_features": [],
        },
        "state_flags": {
            "is_dead": False,
            "is_present_in_scene": False,
            "attitude_towards_party": "neutral",
            "has_met_party": False,
            "player_visibility": visibility,
            "hidden_from_players": hidden,
        },
    }


def _location_document() -> dict:
    return {
        "metadata": {"type": "LOCATION", "version": "1.0.0"},
        "identity": {"name": "Tavern", "location_type": "interior"},
        "narrative_profile": {
            "public_description": "A cozy tavern",
            "secret_lore_master": "Secret back room",
            "illustration_url": "/api/v1/entities/test/illustration",
        },
        "state_flags": {
            "is_accessible_to_party": True,
            "danger_level": 1,
            "is_destroyed": False,
        },
    }


def _make_entity(
    *,
    entity_type: str = "NPC",
    document: dict | None = None,
    campaign_id: uuid.UUID | None = None,
) -> CampaignEntity:
    now = datetime.now(UTC)
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=campaign_id or uuid.uuid4(),
        entity_type=entity_type,
        document=document or _npc_document(),
        created_at=now,
        updated_at=now,
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


class TestIllustrationVisibilityRules:
    def test_player_can_view_visible_npc(self):
        entity = _make_entity(document=_npc_document(visibility="visible"))
        assert player_can_view_entity_illustration(entity) is True

    def test_player_cannot_view_unknown_npc(self):
        entity = _make_entity(document=_npc_document(visibility="unknown"))
        assert player_can_view_entity_illustration(entity) is False

    def test_player_cannot_view_hidden_npc(self):
        entity = _make_entity(document=_npc_document(visibility="hidden"))
        assert player_can_view_entity_illustration(entity) is False

    def test_player_can_always_view_location(self):
        entity = _make_entity(entity_type="LOCATION", document=_location_document())
        assert player_can_view_entity_illustration(entity) is True

    def test_mask_unknown_npc_strips_illustration_url(self):
        document = _npc_document(visibility="unknown")
        document["ai_narrative_profile"]["illustration_url"] = "/api/v1/entities/x/illustration"
        masked = mask_hidden_npc_document(document)
        profile = masked["ai_narrative_profile"]
        assert "illustration_url" not in profile

    def test_read_and_write_npc_illustration_url(self):
        entity = _make_entity()
        write_entity_illustration_url(entity, "/api/v1/entities/x/illustration")
        assert read_entity_illustration_url(entity) == "/api/v1/entities/x/illustration"

    def test_write_location_illustration_url(self):
        entity = _make_entity(entity_type="LOCATION", document=_location_document())
        write_entity_illustration_url(entity, "https://example.com/tavern.png")
        profile = entity.document["narrative_profile"]
        assert profile["illustration_url"] == "https://example.com/tavern.png"


@pytest.mark.asyncio
async def test_player_cannot_get_hidden_npc_illustration(override_db, mock_db):
    user = _make_user()
    entity = _make_entity(document=_npc_document(visibility="unknown"))
    _override_user(user)

    mock_db.scalar = AsyncMock(return_value=entity)

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"):
        with patch(
            "app.api.routes.entities.resolve_entity_illustration_storage",
            return_value=("camp/illustrations/fake.png", "image/png"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/entities/{entity.id}/illustration")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_player_can_get_location_illustration(override_db, mock_db):
    user = _make_user()
    entity = _make_entity(entity_type="LOCATION", document=_location_document())
    _override_user(user)

    mock_db.scalar = AsyncMock(return_value=entity)

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"):
        with patch(
            "app.api.routes.entities.resolve_entity_illustration_storage",
            return_value=("camp/illustrations/fake.png", "image/png"),
        ):
            with patch("app.api.routes.entities.get_storage_backend") as mock_storage_factory:
                mock_storage = mock_storage_factory.return_value
                mock_storage.get_object.return_value = b"img"
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/entities/{entity.id}/illustration")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_master_can_upload_illustration(override_db, mock_db):
    user = _make_user()
    entity = _make_entity()
    _override_user(user)

    mock_db.scalar = AsyncMock(return_value=entity)

    async def fake_save(db, ent, **kwargs):
        profile = dict(ent.document["ai_narrative_profile"])
        profile["illustration_url"] = f"/api/v1/entities/{ent.id}/illustration"
        document = dict(ent.document)
        document["ai_narrative_profile"] = profile
        ent.document = document
        return profile["illustration_url"]

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="MASTER"):
        with patch(
            "app.api.routes.entities.save_entity_illustration_file",
            new_callable=AsyncMock,
            side_effect=fake_save,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/entities/{entity.id}/illustration",
                    files={"file": ("portrait.png", BytesIO(b"fake-png"), "image/png")},
                )

    assert response.status_code == 200
    assert response.json()["document"]["ai_narrative_profile"]["illustration_url"].endswith("/illustration")


@pytest.mark.asyncio
async def test_avatar_upload_preserves_illustration_url(tmp_path):
    from unittest.mock import AsyncMock

    from app.core.config import settings
    from app.services.entity_avatars import read_entity_avatar_url, save_entity_avatar_file

    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)
    try:
        entity = _make_entity()
        illustration_path = f"/api/v1/entities/{entity.id}/illustration"
        write_entity_illustration_url(entity, illustration_path)

        mock_db = AsyncMock()
        await save_entity_avatar_file(
            mock_db,
            entity,
            original_name="avatar.png",
            content=b"fake-png",
            mime_type="image/png",
        )

        assert read_entity_illustration_url(entity) == illustration_path
        assert read_entity_avatar_url(entity) == f"/api/v1/entities/{entity.id}/avatar"
    finally:
        settings.upload_dir = original_upload_dir


@pytest.mark.asyncio
async def test_resolve_illustration_storage_finds_uploaded_file(tmp_path):
    from app.core.config import settings
    from app.services.entity_illustrations import (
        illustration_api_path,
        resolve_entity_illustration_storage,
        save_entity_illustration_file,
    )
    from app.services.object_storage import get_storage_backend
    from unittest.mock import AsyncMock

    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)
    try:
        entity = _make_entity()
        mock_db = AsyncMock()
        await save_entity_illustration_file(
            mock_db,
            entity,
            original_name="portrait.png",
            content=b"fake-png",
            mime_type="image/png",
        )

        assert read_entity_illustration_url(entity) == illustration_api_path(entity.id)
        resolved = resolve_entity_illustration_storage(entity)
        assert resolved is not None
        key, media_type = resolved
        assert media_type == "image/png"
        storage = get_storage_backend()
        assert storage.get_object(key) == b"fake-png"
    finally:
        settings.upload_dir = original_upload_dir


@pytest.mark.asyncio
async def test_master_can_get_npc_illustration_file(override_db, mock_db, tmp_path):
    from app.core.config import settings
    from app.services.entity_illustrations import save_entity_illustration_file
    from unittest.mock import AsyncMock

    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)
    try:
        user = _make_user()
        entity = _make_entity(document=_npc_document(visibility="visible"))
        _override_user(user)

        mock_db.scalar = AsyncMock(return_value=entity)
        await save_entity_illustration_file(
            mock_db,
            entity,
            original_name="portrait.png",
            content=b"fake-png",
            mime_type="image/png",
        )

        with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="MASTER"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/entities/{entity.id}/illustration")

        assert response.status_code == 200
        assert response.content == b"fake-png"
    finally:
        settings.upload_dir = original_upload_dir


@pytest.mark.asyncio
async def test_player_can_upload_own_pc_illustration(override_db, mock_db):
    player_id = uuid.uuid4()
    user = _make_user(user_id=player_id)
    entity = _make_entity(entity_type="PC", document=_pc_document(user_id=player_id))
    _override_user(user)

    mock_db.scalar = AsyncMock(return_value=entity)

    async def fake_save(db, ent, **kwargs):
        write_entity_illustration_url(ent, f"/api/v1/entities/{ent.id}/illustration")
        return f"/api/v1/entities/{ent.id}/illustration"

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"):
        with patch(
            "app.api.routes.entities.save_entity_illustration_file",
            new_callable=AsyncMock,
            side_effect=fake_save,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/entities/{entity.id}/illustration",
                    files={"file": ("portrait.png", BytesIO(b"fake-png"), "image/png")},
                )

    assert response.status_code == 200
    assert response.json()["document"]["public_profile"]["illustration_url"].endswith("/illustration")


@pytest.mark.asyncio
async def test_player_can_upload_own_pc_avatar(override_db, mock_db):
    player_id = uuid.uuid4()
    user = _make_user(user_id=player_id)
    entity = _make_entity(entity_type="PC", document=_pc_document(user_id=player_id))
    _override_user(user)

    mock_db.scalar = AsyncMock(return_value=entity)

    async def fake_save(db, ent, **kwargs):
        profile = dict(ent.document["public_profile"])
        profile["avatar_url"] = f"/api/v1/entities/{ent.id}/avatar"
        document = dict(ent.document)
        document["public_profile"] = profile
        ent.document = document
        return profile["avatar_url"]

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"):
        with patch(
            "app.api.routes.entities.save_entity_avatar_file",
            new_callable=AsyncMock,
            side_effect=fake_save,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/entities/{entity.id}/avatar",
                    files={"file": ("avatar.png", BytesIO(b"fake-png"), "image/png")},
                )

    assert response.status_code == 200
    assert response.json()["document"]["public_profile"]["avatar_url"].endswith("/avatar")


@pytest.mark.asyncio
async def test_player_cannot_upload_npc_illustration(override_db, mock_db):
    user = _make_user()
    entity = _make_entity(document=_npc_document(visibility="visible"))
    _override_user(user)

    mock_db.scalar = AsyncMock(return_value=entity)

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/entities/{entity.id}/illustration",
                files={"file": ("portrait.png", BytesIO(b"fake-png"), "image/png")},
            )

    assert response.status_code == 403
    assert "master" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_cannot_upload_other_pc_illustration(override_db, mock_db):
    owner_id = uuid.uuid4()
    other_player = _make_user()
    entity = _make_entity(entity_type="PC", document=_pc_document(user_id=owner_id))
    _override_user(other_player)

    mock_db.scalar = AsyncMock(return_value=entity)

    with patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/entities/{entity.id}/illustration",
                files={"file": ("portrait.png", BytesIO(b"fake-png"), "image/png")},
            )

    assert response.status_code == 403
    assert "own character" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_cannot_upload_scene_message_image(override_db, mock_db):
    user = _make_user()
    scene = _make_scene()
    _override_user(user)

    mock_db.scalar = AsyncMock(return_value=scene)

    with (
        patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"),
        patch("app.api.routes.scenes.get_scene_by_id", new_callable=AsyncMock, return_value=scene),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/scenes/{scene.id}/message-images",
                files={"file": ("map.png", BytesIO(b"fake-png"), "image/png")},
            )

    assert response.status_code == 403
    assert "master" in response.json()["detail"].lower()


def _make_scene(campaign_id: uuid.UUID | None = None):
    from app.models.campaign import Scene

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

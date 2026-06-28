import uuid
from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.campaign import CampaignEntity
from app.models.user import User
from app.schemas.entities import CharacterSheetUpsert, TypedSystemMechanics
from app.services.entities import (
    INSPIRATION_GRANT_FORBIDDEN,
    CharacterSheetError,
    assert_player_may_set_inspiration,
)

from tests.test_character_sheets import _frontend_dnd5e_sheet, _pc_document_with_typed_sheet


def _make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="player@test.com",
        password_hash="hash",
        display_name="Player",
    )


def _make_pc_entity(*, inspiration: bool) -> CampaignEntity:
    sheet = _frontend_dnd5e_sheet()
    sheet["roleplay"]["inspiration"] = inspiration
    document = _pc_document_with_typed_sheet(sheet)
    now = datetime.now(timezone.utc)
    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        entity_type="PC",
        document=document,
        created_at=now,
        updated_at=now,
    )


def _character_sheet_upsert(*, inspiration: bool) -> CharacterSheetUpsert:
    sheet = _frontend_dnd5e_sheet()
    sheet["roleplay"]["inspiration"] = inspiration
    return CharacterSheetUpsert(
        identity={
            "name": "Aldric",
            "concept": "Fighter",
            "faction_id": None,
            "current_location_id": None,
        },
        system_mechanics=TypedSystemMechanics(
            system_id="dnd5e",
            schema_version="1.0.0",
            sheet=sheet,
        ),
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


class TestInspirationPermissionRules:
    def test_player_cannot_grant_on_new_sheet(self):
        sheet = _frontend_dnd5e_sheet()
        sheet["roleplay"]["inspiration"] = True
        with pytest.raises(CharacterSheetError, match=INSPIRATION_GRANT_FORBIDDEN):
            assert_player_may_set_inspiration(existing=None, new_sheet=sheet)

    def test_player_can_create_without_inspiration(self):
        sheet = _frontend_dnd5e_sheet()
        assert_player_may_set_inspiration(existing=None, new_sheet=sheet)

    def test_player_cannot_grant_when_had_none(self):
        existing = _make_pc_entity(inspiration=False)
        sheet = deepcopy(existing.document["system_mechanics"]["sheet"])
        sheet["roleplay"]["inspiration"] = True
        with pytest.raises(CharacterSheetError, match=INSPIRATION_GRANT_FORBIDDEN):
            assert_player_may_set_inspiration(existing=existing, new_sheet=sheet)

    def test_player_can_spend_inspiration(self):
        existing = _make_pc_entity(inspiration=True)
        sheet = deepcopy(existing.document["system_mechanics"]["sheet"])
        sheet["roleplay"]["inspiration"] = False
        assert_player_may_set_inspiration(existing=existing, new_sheet=sheet)

    def test_player_can_save_without_changing_inspiration(self):
        existing = _make_pc_entity(inspiration=True)
        sheet = deepcopy(existing.document["system_mechanics"]["sheet"])
        assert_player_may_set_inspiration(existing=existing, new_sheet=sheet)


@pytest.mark.asyncio
async def test_player_put_my_sheet_grant_returns_403(override_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    _override_user(user)
    payload = _character_sheet_upsert(inspiration=True)

    with (
        patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"),
        patch(
            "app.api.routes.character_sheets.upsert_player_character_sheet",
            new_callable=AsyncMock,
            side_effect=CharacterSheetError(INSPIRATION_GRANT_FORBIDDEN),
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/campaigns/{campaign_id}/my-sheet",
                json=payload.model_dump(mode="json"),
            )

    assert response.status_code == 403
    assert response.json()["detail"] == INSPIRATION_GRANT_FORBIDDEN


@pytest.mark.asyncio
async def test_player_put_my_sheet_spend_allowed(override_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    _override_user(user)
    payload = _character_sheet_upsert(inspiration=False)

    now = datetime.now(timezone.utc)
    saved_entity = CampaignEntity(
        id=entity_id,
        campaign_id=campaign_id,
        entity_type="PC",
        document=_pc_document_with_typed_sheet(_frontend_dnd5e_sheet()),
        created_at=now,
        updated_at=now,
    )

    with (
        patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="PLAYER"),
        patch(
            "app.api.routes.character_sheets.upsert_player_character_sheet",
            new_callable=AsyncMock,
            return_value=(saved_entity, []),
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/campaigns/{campaign_id}/my-sheet",
                json=payload.model_dump(mode="json"),
            )

    assert response.status_code == 200
    assert response.json()["id"] == str(entity_id)


@pytest.mark.asyncio
async def test_master_entity_put_can_grant_inspiration(override_db, mock_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    _override_user(user)

    sheet = _frontend_dnd5e_sheet()
    sheet["roleplay"]["inspiration"] = True
    document = _pc_document_with_typed_sheet(sheet)
    now = datetime.now(timezone.utc)
    entity = CampaignEntity(
        id=entity_id,
        campaign_id=campaign_id,
        entity_type="PC",
        document=document,
        created_at=now,
        updated_at=now,
    )

    with (
        patch("app.api.deps.get_user_campaign_role", new_callable=AsyncMock, return_value="MASTER"),
        patch("app.api.routes.entities._get_entity_or_404", new_callable=AsyncMock, return_value=entity),
        patch("app.api.routes.entities.get_campaign_or_error", new_callable=AsyncMock) as get_campaign,
        patch("app.api.routes.entities.validate_entity_cross_references", new_callable=AsyncMock),
    ):
        campaign = AsyncMock()
        campaign.game_system = "dnd5e"
        get_campaign.return_value = campaign
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/entities/{entity_id}",
                json={"document": document},
            )

    assert response.status_code == 200
    assert response.json()["document"]["system_mechanics"]["sheet"]["roleplay"]["inspiration"] is True

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from app.models.monster_catalog import SystemMonsterCatalog
from app.models.user import User

SNAPSHOT_PATH = __import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "dnd5e" / "srd-monsters.json"


@pytest.fixture
def goblin_catalog_entry() -> SystemMonsterCatalog:
    monsters = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    goblin = next(creature for creature in monsters if creature.get("key") == "srd_goblin")
    from app.core.seed_monsters import build_catalog_row

    return SystemMonsterCatalog(**build_catalog_row(goblin))


@pytest.fixture
def mock_user() -> User:
    user = MagicMock(spec=User)
    user.id = __import__("uuid").uuid4()
    return user


@pytest.fixture
def override_auth(mock_user):
    from app.api.deps import get_current_user

    async def _user():
        return mock_user

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_db():
    db = AsyncMock()

    async def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_search_catalog_monsters(override_auth, override_db, goblin_catalog_entry):
    scalars_result = MagicMock()
    scalars_result.all.return_value = [goblin_catalog_entry]
    override_db.scalars = AsyncMock(return_value=scalars_result)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/catalog/monsters", params={"system_id": "dnd5e", "q": "goblin"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slug"] == "goblin"
    assert body[0]["name"] == "Goblin"


@pytest.mark.asyncio
async def test_spawn_monsters_master_only(override_auth, override_db, mock_user, goblin_catalog_entry):
    campaign_id = __import__("uuid").uuid4()
    entity = MagicMock()
    entity.id = __import__("uuid").uuid4()

    with patch("app.api.routes.monster_catalog.require_campaign_master", new=AsyncMock()) as master_check, patch(
        "app.api.routes.monster_catalog.spawn_monsters",
        new=AsyncMock(return_value=[entity]),
    ) as spawn_mock:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/campaigns/{campaign_id}/monsters/spawn",
                json={"slug": "goblin", "count": 2, "hidden": True},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["created"] == [str(entity.id)]
    master_check.assert_awaited_once()
    spawn_mock.assert_awaited_once()

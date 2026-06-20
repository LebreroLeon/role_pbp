import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.entities import EntityType
from app.services.entities import (
    EntityReferenceError,
    ensure_single_arc_manifest,
    validate_entity_cross_references,
)


def _mock_db_with_entities(*entities: MagicMock) -> AsyncMock:
    db = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.all.return_value = list(entities)
    db.scalars = AsyncMock(return_value=scalars_result)
    return db


def _entity_row(*, entity_id: uuid.UUID, campaign_id: uuid.UUID, entity_type: str) -> MagicMock:
    row = MagicMock()
    row.id = entity_id
    row.campaign_id = campaign_id
    row.entity_type = entity_type
    return row


@pytest.mark.asyncio
async def test_validate_accepts_null_faction_and_location():
    campaign_id = uuid.uuid4()
    db = _mock_db_with_entities()

    document = {
        "identity": {
            "name": "NPC",
            "concept": "Test",
            "faction_id": None,
            "current_location_id": None,
        }
    }

    await validate_entity_cross_references(
        db,
        campaign_id=campaign_id,
        entity_type=EntityType.NPC,
        document=document,
    )


@pytest.mark.asyncio
async def test_validate_rejects_missing_faction_reference():
    campaign_id = uuid.uuid4()
    missing_faction = uuid.uuid4()
    db = _mock_db_with_entities()

    document = {
        "identity": {
            "name": "NPC",
            "concept": "Test",
            "faction_id": str(missing_faction),
            "current_location_id": "",
        }
    }

    with pytest.raises(EntityReferenceError, match="identity.faction_id"):
        await validate_entity_cross_references(
            db,
            campaign_id=campaign_id,
            entity_type=EntityType.NPC,
            document=document,
        )


@pytest.mark.asyncio
async def test_validate_accepts_existing_location_reference():
    campaign_id = uuid.uuid4()
    location_id = uuid.uuid4()
    location = _entity_row(entity_id=location_id, campaign_id=campaign_id, entity_type="LOCATION")
    db = _mock_db_with_entities(location)

    document = {
        "identity": {
            "name": "PC",
            "concept": "Hero",
            "faction_id": None,
            "current_location_id": str(location_id),
        }
    }

    await validate_entity_cross_references(
        db,
        campaign_id=campaign_id,
        entity_type=EntityType.PC,
        document=document,
    )


@pytest.mark.asyncio
async def test_validate_rejects_wrong_entity_type_for_location():
    campaign_id = uuid.uuid4()
    npc_id = uuid.uuid4()
    npc = _entity_row(entity_id=npc_id, campaign_id=campaign_id, entity_type="NPC")
    db = _mock_db_with_entities(npc)

    document = {
        "identity": {
            "name": "PC",
            "concept": "Hero",
            "current_location_id": str(npc_id),
        }
    }

    with pytest.raises(EntityReferenceError, match="expected LOCATION"):
        await validate_entity_cross_references(
            db,
            campaign_id=campaign_id,
            entity_type=EntityType.PC,
            document=document,
        )


@pytest.mark.asyncio
async def test_validate_relationship_source_and_target():
    campaign_id = uuid.uuid4()
    source_id = uuid.uuid4()
    target_id = uuid.uuid4()
    source = _entity_row(entity_id=source_id, campaign_id=campaign_id, entity_type="NPC")
    target = _entity_row(entity_id=target_id, campaign_id=campaign_id, entity_type="FACTION")
    db = _mock_db_with_entities(source, target)

    document = {
        "connection": {
            "source_id": str(source_id),
            "target_id": str(target_id),
            "is_bidirectional": True,
        }
    }

    await validate_entity_cross_references(
        db,
        campaign_id=campaign_id,
        entity_type=EntityType.RELATIONSHIP,
        document=document,
    )


@pytest.mark.asyncio
async def test_validate_relationship_cannot_reference_self():
    campaign_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    db = AsyncMock()

    document = {
        "connection": {
            "source_id": str(entity_id),
            "target_id": str(uuid.uuid4()),
            "is_bidirectional": True,
        }
    }

    with pytest.raises(EntityReferenceError, match="cannot reference itself"):
        await validate_entity_cross_references(
            db,
            campaign_id=campaign_id,
            entity_type=EntityType.RELATIONSHIP,
            document=document,
            entity_id=entity_id,
        )


@pytest.mark.asyncio
async def test_ensure_single_arc_manifest_rejects_duplicate():
    campaign_id = uuid.uuid4()
    db = AsyncMock()
    db.scalar.return_value = uuid.uuid4()

    with pytest.raises(EntityReferenceError, match="Only one ARC_MANIFEST"):
        await ensure_single_arc_manifest(
            db,
            campaign_id=campaign_id,
            entity_type=EntityType.ARC_MANIFEST,
        )


@pytest.mark.asyncio
async def test_ensure_single_arc_manifest_allows_first():
    campaign_id = uuid.uuid4()
    db = AsyncMock()
    db.scalar.return_value = None

    await ensure_single_arc_manifest(
        db,
        campaign_id=campaign_id,
        entity_type=EntityType.ARC_MANIFEST,
    )

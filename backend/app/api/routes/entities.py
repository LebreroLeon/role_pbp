import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.campaign import Campaign, CampaignEntity
from app.schemas.entities import EntityCreate, EntityResponse, EntityType, EntityUpdate
from app.services.entities import EntityValidationError, strip_master_secrets, validate_entity_document

router = APIRouter(prefix="/entities", tags=["entities"])


def _entity_to_response(entity: CampaignEntity, *, include_secrets: bool) -> EntityResponse:
    document = entity.document
    if not include_secrets:
        document = strip_master_secrets(document, EntityType(entity.entity_type))

    return EntityResponse(
        id=str(entity.id),
        campaign_id=str(entity.campaign_id),
        entity_type=EntityType(entity.entity_type),
        document=document,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(payload: EntityCreate, db: AsyncSession = Depends(get_db)) -> EntityResponse:
    try:
        campaign_id = uuid.UUID(payload.campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid campaign_id") from exc

    try:
        validated = validate_entity_document(payload.entity_type, payload.document)
    except EntityValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        campaign = Campaign(id=campaign_id, name=f"Campaign {campaign_id}")
        db.add(campaign)

    entity = CampaignEntity(
        campaign_id=campaign_id,
        entity_type=payload.entity_type.value,
        document=validated.model_dump(mode="json"),
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return _entity_to_response(entity, include_secrets=True)


@router.get("", response_model=list[EntityResponse])
async def list_entities(
    campaign_id: str = Query(...),
    entity_type: EntityType | None = Query(None),
    include_secrets: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> list[EntityResponse]:
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid campaign_id") from exc

    query = select(CampaignEntity).where(CampaignEntity.campaign_id == campaign_uuid)
    if entity_type is not None:
        query = query.where(CampaignEntity.entity_type == entity_type.value)

    entities = (await db.scalars(query.order_by(CampaignEntity.created_at))).all()
    return [_entity_to_response(entity, include_secrets=include_secrets) for entity in entities]


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    include_secrets: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    entity = await _get_entity_or_404(entity_id, db)
    return _entity_to_response(entity, include_secrets=include_secrets)


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    payload: EntityUpdate,
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    entity = await _get_entity_or_404(entity_id, db)

    try:
        validated = validate_entity_document(EntityType(entity.entity_type), payload.document)
    except EntityValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    entity.document = validated.model_dump(mode="json")
    await db.commit()
    await db.refresh(entity)
    return _entity_to_response(entity, include_secrets=True)


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(entity_id: str, db: AsyncSession = Depends(get_db)) -> None:
    entity = await _get_entity_or_404(entity_id, db)
    await db.delete(entity)
    await db.commit()


async def _get_entity_or_404(entity_id: str, db: AsyncSession) -> CampaignEntity:
    try:
        entity_uuid = uuid.UUID(entity_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid entity_id") from exc

    entity = await db.scalar(select(CampaignEntity).where(CampaignEntity.id == entity_uuid))
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

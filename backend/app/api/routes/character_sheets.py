from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, parse_uuid, require_campaign_master, require_campaign_member
from app.core.database import get_db
from app.models.campaign import CampaignEntity
from app.models.user import User
from app.schemas.entities import CharacterSheetUpsert, ContextualRollRequest, EntityResponse, EntityType
from app.services.entities import (
    CharacterSheetError,
    EntityValidationError,
    find_pc_by_user,
    list_campaign_pc_sheets,
    roll_player_character_contextual,
    strip_master_secrets,
    upsert_player_character_sheet,
)
from app.services.scenes import get_active_scene
from app.services.scene_ws import broadcast_scene_update

router = APIRouter(prefix="/campaigns", tags=["character-sheets"])


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


def _sheet_error_to_http(exc: CharacterSheetError | EntityValidationError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail.lower():
        return HTTPException(status_code=404, detail=detail)
    if "multiple player characters" in detail.lower():
        return HTTPException(status_code=409, detail=detail)
    if "only the master can grant inspiration" in detail.lower():
        return HTTPException(status_code=403, detail=detail)
    return HTTPException(status_code=422, detail=detail)


async def _require_campaign_player(
    db: AsyncSession,
    user: User,
    campaign_id,
) -> None:
    role = await require_campaign_member(db, user, campaign_id)
    if role != "PLAYER":
        raise HTTPException(status_code=403, detail="Player role required")


@router.get("/{campaign_id}/my-sheet", response_model=EntityResponse)
async def get_my_character_sheet(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_uuid)

    try:
        pc = await find_pc_by_user(db, campaign_uuid, current_user.id)
    except CharacterSheetError as exc:
        raise _sheet_error_to_http(exc) from exc

    if pc is None:
        raise HTTPException(status_code=404, detail="Character sheet not found")

    return _entity_to_response(pc, include_secrets=True)


@router.put("/{campaign_id}/my-sheet", response_model=EntityResponse)
async def upsert_my_character_sheet(
    campaign_id: str,
    payload: CharacterSheetUpsert,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await _require_campaign_player(db, current_user, campaign_uuid)

    try:
        entity = await upsert_player_character_sheet(
            db,
            campaign_id=campaign_uuid,
            user_id=current_user.id,
            payload=payload,
        )
    except (CharacterSheetError, EntityValidationError) as exc:
        raise _sheet_error_to_http(exc) from exc

    return _entity_to_response(entity, include_secrets=True)


@router.post("/{campaign_id}/my-sheet/roll")
async def roll_my_character_sheet(
    campaign_id: str,
    payload: ContextualRollRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    role = await require_campaign_member(db, current_user, campaign_uuid)

    try:
        roll_result, scene_id = await roll_player_character_contextual(
            db,
            campaign_id=campaign_uuid,
            user_id=current_user.id,
            roll_type=payload.roll_type,
            dice_expression=payload.dice_expression,
            modifier=payload.modifier,
            context=payload.context,
            sender_role=role,
            master_only=payload.master_only,
        )
    except (CharacterSheetError, EntityValidationError) as exc:
        raise _sheet_error_to_http(exc) from exc

    if scene_id is not None:
        scene = await get_active_scene(db, campaign_uuid)
        if scene is not None:
            await broadcast_scene_update(db, scene, requester_role=role)

    return roll_result


@router.get("/{campaign_id}/sheets", response_model=list[EntityResponse])
async def list_campaign_character_sheets(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[EntityResponse]:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_uuid)

    pcs = await list_campaign_pc_sheets(db, campaign_uuid)
    return [_entity_to_response(pc, include_secrets=True) for pc in pcs]

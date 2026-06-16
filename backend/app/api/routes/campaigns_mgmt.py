import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, parse_uuid, require_campaign_member, require_campaign_master
from app.core.database import get_db
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.campaign_mgmt import (
    CampaignCreate,
    CampaignMemberAdd,
    CampaignMemberResponse,
    CampaignResponse,
)
from app.schemas.scene import SceneResponse
from app.services.scenes import SceneServiceError, get_active_scene, list_campaign_scenes, scene_to_response
from app.services.campaigns import (
    CampaignServiceError,
    add_campaign_member,
    create_campaign,
    get_user_campaign_role,
    list_campaign_members,
    list_user_campaigns,
    require_master,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignResponse])
async def get_my_campaigns(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    return await list_user_campaigns(db, current_user.id)


@router.post("", response_model=CampaignResponse, status_code=201)
async def post_campaign(
    payload: CampaignCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    return await create_campaign(db, current_user.id, payload)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid campaign_id") from exc

    role = await get_user_campaign_role(db, current_user.id, campaign_uuid)
    if role is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_uuid))
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return CampaignResponse(
        id=str(campaign.id),
        name=campaign.name,
        tone=campaign.tone,
        game_system=campaign.game_system,
        role=role,
    )


@router.get("/{campaign_id}/members", response_model=list[CampaignMemberResponse])
async def get_members(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[CampaignMemberResponse]:
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid campaign_id") from exc

    role = await get_user_campaign_role(db, current_user.id, campaign_uuid)
    if role is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return await list_campaign_members(db, campaign_uuid)


@router.post("/{campaign_id}/members", response_model=CampaignMemberResponse, status_code=201)
async def post_member(
    campaign_id: str,
    payload: CampaignMemberAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> CampaignMemberResponse:
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid campaign_id") from exc

    try:
        await require_master(db, current_user.id, campaign_uuid)
        return await add_campaign_member(db, campaign_uuid, payload)
    except CampaignServiceError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/{campaign_id}/scenes", response_model=list[SceneResponse])
async def get_campaign_scenes(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[SceneResponse]:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_uuid)
    return await list_campaign_scenes(db, campaign_uuid)


@router.get("/{campaign_id}/scenes/active", response_model=SceneResponse)
async def get_active_campaign_scene(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_uuid)

    scene = await get_active_scene(db, campaign_uuid)
    if scene is None:
        raise HTTPException(status_code=404, detail="No active scene")

    return scene_to_response(scene)

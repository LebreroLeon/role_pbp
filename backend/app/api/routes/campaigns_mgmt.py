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
    CampaignUpdate,
)
from app.schemas.scene import ActivateSceneRequest, MasterBriefingResponse, SceneResponse
from app.schemas.unread import UnreadCountsResponse
from app.services.scenes import (
    SceneServiceError,
    ensure_player_pc_present_in_scene,
    get_active_scene,
    get_master_briefing,
    get_scene_by_id,
    list_campaign_scenes,
    scene_to_response,
    start_active_scene,
)
from app.services.unread_counts import get_unread_counts, mark_ooc_read
from app.services.campaign_ws import campaign_ws_manager
from app.services.campaigns import (
    CampaignServiceError,
    add_campaign_member,
    create_campaign,
    delete_campaign,
    get_user_campaign_role,
    list_campaign_members,
    list_user_campaigns,
    remove_campaign_member,
    require_master,
    update_campaign,
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


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def patch_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_uuid)
    try:
        return await update_campaign(db, campaign_uuid, current_user.id, payload)
    except CampaignServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign_route(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_uuid)
    try:
        await delete_campaign(db, campaign_uuid)
    except CampaignServiceError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.delete("/{campaign_id}/members/{user_id}", status_code=204)
async def delete_campaign_member(
    campaign_id: str,
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    member_uuid = parse_uuid(user_id, "user_id")
    await require_campaign_master(db, current_user, campaign_uuid)
    try:
        await remove_campaign_member(db, campaign_uuid, member_uuid)
    except CampaignServiceError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


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
    role = await require_campaign_member(db, current_user, campaign_uuid)
    return await list_campaign_scenes(db, campaign_uuid, viewer_role=role)


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

    if scene.status == "ACTIVE":
        await ensure_player_pc_present_in_scene(db, scene, current_user.id)

    role = await require_campaign_member(db, current_user, campaign_uuid)
    return scene_to_response(scene, viewer_role=role)


@router.get("/{campaign_id}/unread-counts", response_model=UnreadCountsResponse)
async def get_campaign_unread_counts(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> UnreadCountsResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    role = await require_campaign_member(db, current_user, campaign_uuid)
    return await get_unread_counts(db, campaign_uuid, current_user.id, viewer_role=role)


@router.post("/{campaign_id}/ooc/read", status_code=204)
async def mark_campaign_ooc_read(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_uuid)
    await mark_ooc_read(db, campaign_uuid, current_user.id)
    await campaign_ws_manager.broadcast_unread_counts(db, campaign_id)


@router.get("/{campaign_id}/scenes/{scene_id}/master-briefing", response_model=MasterBriefingResponse)
async def get_scene_master_briefing(
    campaign_id: str,
    scene_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MasterBriefingResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    scene_uuid = parse_uuid(scene_id, "scene_id")
    await require_campaign_master(db, current_user, campaign_uuid)

    scene = await get_scene_by_id(db, scene_uuid)
    if scene is None or scene.campaign_id != campaign_uuid:
        raise HTTPException(status_code=404, detail="Scene not found")

    return await get_master_briefing(db, scene)


@router.post("/{campaign_id}/scenes/{scene_id}/activate", response_model=SceneResponse)
async def start_active_campaign_scene(
    campaign_id: str,
    scene_id: str,
    payload: ActivateSceneRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    scene_uuid = parse_uuid(scene_id, "scene_id")
    await require_campaign_master(db, current_user, campaign_uuid)

    scene = await get_scene_by_id(db, scene_uuid)
    if scene is None or scene.campaign_id != campaign_uuid:
        raise HTTPException(status_code=404, detail="Scene not found")

    try:
        from app.services.scene_ws import broadcast_scene_update

        await start_active_scene(
            db,
            scene,
            send_opening_to_chat=payload.send_opening_to_chat,
            activator_user_id=str(current_user.id),
        )
        return await broadcast_scene_update(db, scene, requester_role="MASTER")
    except SceneServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

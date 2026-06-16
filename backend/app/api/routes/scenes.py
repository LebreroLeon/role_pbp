import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_scene_for_member,
    parse_uuid,
    require_campaign_master,
    require_campaign_member,
    scene_service_error_to_http,
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.scene import (
    DiceRollRequest,
    MarkReadRequest,
    PostMessageRequest,
    SceneCreate,
    SceneResponse,
    SceneStatusUpdate,
)
from app.services.scene_ws import scene_ws_manager
from app.services.scenes import (
    SceneServiceError,
    create_scene,
    mark_messages_read,
    post_message,
    roll_scene_dice,
    scene_to_response,
    update_scene_status,
)

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("", response_model=SceneResponse, status_code=201)
async def create_scene_route(
    payload: SceneCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    campaign_id = parse_uuid(payload.campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_id)

    try:
        response = await create_scene(db, campaign_id, payload, current_user.id)
        await scene_ws_manager.broadcast(
            response.id,
            {"event": "scene_update", "scene": response.model_dump(mode="json")},
        )
        return response
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene_route(
    scene_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    return scene_to_response(scene)


@router.post("/{scene_id}/messages", response_model=SceneResponse)
async def post_message_route(
    scene_id: str,
    payload: PostMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    role = await require_campaign_member(db, current_user, scene.campaign_id)
    try:
        response = await post_message(db, scene, str(current_user.id), payload, sender_role=role)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/dice", response_model=SceneResponse)
async def roll_scene_dice_route(
    scene_id: str,
    payload: DiceRollRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    try:
        response = await roll_scene_dice(db, scene, str(current_user.id), payload)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/read", response_model=SceneResponse)
async def mark_read_route(
    scene_id: str,
    payload: MarkReadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    response = await mark_messages_read(
        db,
        scene,
        str(current_user.id),
        payload.message_ids,
    )
    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.patch("/{scene_id}/status", response_model=SceneResponse)
async def patch_scene_status_route(
    scene_id: str,
    payload: SceneStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    response = await update_scene_status(db, scene, payload.status)
    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response

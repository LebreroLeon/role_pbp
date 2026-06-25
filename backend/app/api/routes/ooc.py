from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, parse_uuid, require_campaign_master, require_campaign_member
from app.core.database import get_db
from app.models.user import User
from app.schemas.ooc import OocMessageResponse, OocPublicMessageCreate, OocWhisperMessageCreate
from app.services.campaign_ws import campaign_ws_manager
from app.services.ooc import (
    OocServiceError,
    delete_ooc_message,
    list_ooc_messages,
    post_ooc_public,
    post_ooc_whisper as create_ooc_whisper,
)

router = APIRouter(prefix="/campaigns", tags=["ooc"])


def _ooc_error_to_http(exc: OocServiceError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail.lower():
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@router.get("/{campaign_id}/ooc/messages", response_model=list[OocMessageResponse])
async def get_ooc_messages(
    campaign_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    channel: str | None = None,
) -> list[OocMessageResponse]:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_uuid)
    try:
        return await list_ooc_messages(db, campaign_uuid, current_user.id, channel=channel)
    except OocServiceError as exc:
        raise _ooc_error_to_http(exc) from exc


@router.post("/{campaign_id}/ooc/messages", response_model=OocMessageResponse, status_code=201)
async def post_ooc_message(
    campaign_id: str,
    payload: OocPublicMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> OocMessageResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_uuid)
    try:
        message = await post_ooc_public(db, campaign_uuid, current_user.id, payload.content)
    except OocServiceError as exc:
        raise _ooc_error_to_http(exc) from exc

    await campaign_ws_manager.broadcast_ooc_message(
        campaign_id,
        message.model_dump(mode="json"),
    )
    await campaign_ws_manager.broadcast_unread_counts(db, campaign_id)
    return message


@router.post("/{campaign_id}/ooc/whispers", response_model=OocMessageResponse, status_code=201)
async def create_ooc_whisper_message(
    campaign_id: str,
    payload: OocWhisperMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> OocMessageResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    target_uuid = parse_uuid(payload.target_user_id, "target_user_id")
    await require_campaign_member(db, current_user, campaign_uuid)
    try:
        message = await create_ooc_whisper(
            db,
            campaign_uuid,
            current_user.id,
            target_uuid,
            payload.content,
        )
    except OocServiceError as exc:
        raise _ooc_error_to_http(exc) from exc

    await campaign_ws_manager.broadcast_ooc_message(
        campaign_id,
        message.model_dump(mode="json"),
    )
    await campaign_ws_manager.broadcast_unread_counts(db, campaign_id)
    return message


@router.delete("/{campaign_id}/ooc/messages/{message_id}", status_code=204)
async def delete_ooc_message_route(
    campaign_id: str,
    message_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Response:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    message_uuid = parse_uuid(message_id, "message_id")
    await require_campaign_master(db, current_user, campaign_uuid)
    try:
        deleted = await delete_ooc_message(db, campaign_uuid, message_uuid)
    except OocServiceError as exc:
        raise _ooc_error_to_http(exc) from exc

    await campaign_ws_manager.broadcast_ooc_message_deleted(campaign_id, deleted)
    await campaign_ws_manager.broadcast_unread_counts(db, campaign_id)
    return Response(status_code=204)

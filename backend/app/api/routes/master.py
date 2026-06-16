from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, parse_uuid, require_campaign_master
from app.core.database import get_db
from app.models.user import User
from app.schemas.master import MasterAssistRequest, MasterAssistResponse
from app.services.master import build_master_assist_response
from app.services.scenes import get_scene_by_id

router = APIRouter(prefix="/master", tags=["master"])


@router.post("/assist", response_model=MasterAssistResponse)
async def master_assist(
    payload: MasterAssistRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MasterAssistResponse:
    campaign_id = parse_uuid(payload.campaign_id, "campaign_id")
    scene_id = parse_uuid(payload.scene_id, "scene_id")

    await require_campaign_master(db, current_user, campaign_id)

    scene = await get_scene_by_id(db, scene_id)
    if scene is None or scene.campaign_id != campaign_id:
        raise HTTPException(status_code=404, detail="Scene not found")

    return await build_master_assist_response(payload)

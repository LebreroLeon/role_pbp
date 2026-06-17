from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, parse_uuid, require_campaign_master
from app.core.database import get_db
from app.core.rate_limit import rate_limiter
from app.models.user import User
from app.schemas.master import MasterAssistRequest, MasterAssistResponse
from app.services.master import build_master_assist_response
from app.services.scenes import get_scene_by_id, load_scene_state

router = APIRouter(prefix="/master", tags=["master"])

MASTER_ASSIST_RATE_LIMIT = 10
MASTER_ASSIST_RATE_WINDOW_SECONDS = 60


@router.post("/assist", response_model=MasterAssistResponse)
async def master_assist(
    payload: MasterAssistRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MasterAssistResponse:
    campaign_id = parse_uuid(payload.campaign_id, "campaign_id")
    scene_id = parse_uuid(payload.scene_id, "scene_id")

    await require_campaign_master(db, current_user, campaign_id)

    rate_key = f"master_assist:{campaign_id}:{current_user.id}"
    if not rate_limiter.allow(
        rate_key,
        limit=MASTER_ASSIST_RATE_LIMIT,
        window_seconds=MASTER_ASSIST_RATE_WINDOW_SECONDS,
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for Shadow Master assist (10 requests per minute).",
        )

    scene = await get_scene_by_id(db, scene_id)
    if scene is None or scene.campaign_id != campaign_id:
        raise HTTPException(status_code=404, detail="Scene not found")

    state = load_scene_state(scene)
    return await build_master_assist_response(
        db,
        payload,
        scene=scene,
        top_k=state.memory_settings.rag_top_k_matches,
    )

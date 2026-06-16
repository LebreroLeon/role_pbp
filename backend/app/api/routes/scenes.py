import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.campaign import Campaign, Scene
from app.schemas.scene import (
    DiceRollRequest,
    PostMessageRequest,
    SceneCreate,
    SceneResponse,
    SceneState,
)
from app.services.dice import roll_dice
from app.services.master import utc_now_iso
from app.services.rag import rag_service

router = APIRouter(prefix="/scenes", tags=["scenes"])


def _scene_to_response(scene: Scene) -> SceneResponse:
    state = SceneState.model_validate(scene.scene_state)
    return SceneResponse(
        id=str(scene.id),
        campaign_id=str(scene.campaign_id),
        status=scene.status,
        scene_state=state,
    )


@router.post("", response_model=SceneResponse, status_code=201)
async def create_scene(payload: SceneCreate, db: AsyncSession = Depends(get_db)) -> SceneResponse:
    try:
        campaign_id = uuid.UUID(payload.campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid campaign_id") from exc

    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        campaign = Campaign(id=campaign_id, name=f"Campaign {campaign_id}")
        db.add(campaign)

    scene_state = SceneState(
        campaign_id=str(campaign_id),
        scene_objective=payload.scene_objective,
        turn_order=payload.turn_order,
        current_turn_player_id=payload.turn_order[0] if payload.turn_order else None,
    )

    scene = Scene(
        campaign_id=campaign_id,
        status="ACTIVE",
        scene_state=scene_state.model_dump(),
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return _scene_to_response(scene)


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene(scene_id: str, db: AsyncSession = Depends(get_db)) -> SceneResponse:
    try:
        scene_uuid = uuid.UUID(scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid scene_id") from exc

    scene = await db.scalar(select(Scene).where(Scene.id == scene_uuid))
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return _scene_to_response(scene)


@router.post("/{scene_id}/messages", response_model=SceneResponse)
async def post_message(
    scene_id: str,
    payload: PostMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await _get_scene_or_404(scene_id, db)
    state = SceneState.model_validate(scene.scene_state)

    message = {
        "timestamp": utc_now_iso(),
        "sender_id": payload.sender_id,
        "type": payload.type,
        "text": payload.text,
    }
    state.chat_buffer.append(message)
    state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]

    scene.scene_state = state.model_dump()
    await db.commit()
    await db.refresh(scene)

    rag_service.index_text(
        campaign_id=state.campaign_id,
        document_id=f"{scene_id}:{len(state.chat_buffer)}",
        text=payload.text,
        metadata={"scene_id": scene_id, "sender_id": payload.sender_id},
    )
    return _scene_to_response(scene)


@router.post("/{scene_id}/dice", response_model=SceneResponse)
async def roll_scene_dice(
    scene_id: str,
    payload: DiceRollRequest,
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await _get_scene_or_404(scene_id, db)
    state = SceneState.model_validate(scene.scene_state)

    try:
        result = roll_dice(payload.dice_expression, payload.modifier)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    message = {
        "timestamp": utc_now_iso(),
        "sender_id": payload.sender_id,
        "type": "DICE_ROLL",
        "text": f"Roll: {payload.dice_expression} => {result['final_result']}",
        "dice_expression": payload.dice_expression,
        "raw_result": result["raw_result"],
        "final_result": result["final_result"],
        "skill_checked": payload.skill_checked,
    }
    state.chat_buffer.append(message)
    state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]

    scene.scene_state = state.model_dump()
    await db.commit()
    await db.refresh(scene)
    return _scene_to_response(scene)


async def _get_scene_or_404(scene_id: str, db: AsyncSession) -> Scene:
    try:
        scene_uuid = uuid.UUID(scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid scene_id") from exc

    scene = await db.scalar(select(Scene).where(Scene.id == scene_uuid))
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene

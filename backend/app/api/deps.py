import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.campaign import Campaign, Scene
from app.models.user import CampaignMember, User
from app.services.auth import get_user_by_id
from app.services.campaigns import get_user_campaign_role
from app.services.scenes import SceneServiceError, get_scene_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_user_from_token(db: AsyncSession, token: str) -> User:
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return await get_user_from_token(db, credentials.credentials)


async def require_campaign_member(
    db: AsyncSession,
    user: User,
    campaign_id: uuid.UUID,
) -> str:
    role = await get_user_campaign_role(db, user.id, campaign_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return role


async def require_campaign_master(
    db: AsyncSession,
    user: User,
    campaign_id: uuid.UUID,
) -> None:
    role = await require_campaign_member(db, user, campaign_id)
    if role != "MASTER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Master role required")


async def require_system_manual_master(
    db: AsyncSession,
    user: User,
    system_id: str,
) -> None:
    is_master = await db.scalar(
        select(CampaignMember.id)
        .join(Campaign, Campaign.id == CampaignMember.campaign_id)
        .where(
            CampaignMember.user_id == user.id,
            CampaignMember.role == "MASTER",
            Campaign.game_system == system_id,
        )
        .limit(1)
    )
    if is_master is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master role required for a campaign using this game system",
        )


async def get_scene_for_member(
    db: AsyncSession,
    user: User,
    scene_id: uuid.UUID,
) -> Scene:
    scene = await get_scene_by_id(db, scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    try:
        await require_campaign_member(db, user, scene.campaign_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found") from exc
        raise

    return scene


def parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


def scene_service_error_to_http(exc: SceneServiceError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail.lower():
        return HTTPException(status_code=404, detail=detail)
    if "already exists" in detail.lower():
        return HTTPException(status_code=409, detail=detail)
    return HTTPException(status_code=400, detail=detail)

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignDocument, CampaignEntity, Scene
from app.models.user import CampaignMember, User
from app.schemas.campaign_mgmt import (
    CampaignCreate,
    CampaignMemberAdd,
    CampaignMemberResponse,
    CampaignResponse,
    CampaignUpdate,
)
from app.services.documents import resolve_document_storage_key
from app.services.object_storage import get_storage_backend
from app.services.rag import rag_service


class CampaignServiceError(ValueError):
    pass


async def list_user_campaigns(db: AsyncSession, user_id: uuid.UUID) -> list[CampaignResponse]:
    rows = await db.execute(
        select(Campaign, CampaignMember.role)
        .join(CampaignMember, CampaignMember.campaign_id == Campaign.id)
        .where(CampaignMember.user_id == user_id)
        .order_by(Campaign.created_at.desc())
    )
    return [
        CampaignResponse(
            id=str(campaign.id),
            name=campaign.name,
            tone=campaign.tone,
            game_system=campaign.game_system,
            role=role,
        )
        for campaign, role in rows.all()
    ]


async def create_campaign(db: AsyncSession, user_id: uuid.UUID, payload: CampaignCreate) -> CampaignResponse:
    campaign = Campaign(
        name=payload.name.strip(),
        tone=payload.tone,
        game_system=payload.game_system,
    )
    db.add(campaign)
    await db.flush()

    membership = CampaignMember(campaign_id=campaign.id, user_id=user_id, role="MASTER")
    db.add(membership)
    await db.commit()
    await db.refresh(campaign)

    return CampaignResponse(
        id=str(campaign.id),
        name=campaign.name,
        tone=campaign.tone,
        game_system=campaign.game_system,
        role="MASTER",
    )


async def get_user_campaign_role(
    db: AsyncSession, user_id: uuid.UUID, campaign_id: uuid.UUID
) -> str | None:
    member = await db.scalar(
        select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == user_id,
        )
    )
    return member.role if member else None


async def require_master(db: AsyncSession, user_id: uuid.UUID, campaign_id: uuid.UUID) -> None:
    role = await get_user_campaign_role(db, user_id, campaign_id)
    if role != "MASTER":
        raise CampaignServiceError("Master role required")


async def add_campaign_member(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    payload: CampaignMemberAdd,
) -> CampaignMemberResponse:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        raise CampaignServiceError("Campaign not found")

    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        raise CampaignServiceError("User not found with that email")

    existing = await db.scalar(
        select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == user.id,
        )
    )
    if existing is not None:
        raise CampaignServiceError("User is already a member of this campaign")

    membership = CampaignMember(campaign_id=campaign_id, user_id=user.id, role=payload.role)
    db.add(membership)
    await db.commit()

    from app.services.entities import find_pc_by_user
    from app.services.scenes import add_player_to_scene_presence, get_active_scene

    active_scene = await get_active_scene(db, campaign_id)
    if active_scene is not None and active_scene.status == "ACTIVE":
        pc = await find_pc_by_user(db, campaign_id, user.id)
        if pc is not None:
            await add_player_to_scene_presence(db, active_scene, user_id=user.id)

    return CampaignMemberResponse(
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=payload.role,
    )


async def list_campaign_members(db: AsyncSession, campaign_id: uuid.UUID) -> list[CampaignMemberResponse]:
    rows = await db.execute(
        select(User, CampaignMember.role)
        .join(CampaignMember, CampaignMember.user_id == User.id)
        .where(CampaignMember.campaign_id == campaign_id)
        .order_by(CampaignMember.joined_at.asc())
    )
    return [
        CampaignMemberResponse(
            user_id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=role,
        )
        for user, role in rows.all()
    ]


async def update_campaign(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: CampaignUpdate,
) -> CampaignResponse:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        raise CampaignServiceError("Campaign not found")

    if payload.name is not None:
        campaign.name = payload.name.strip()
    if payload.tone is not None:
        campaign.tone = payload.tone.strip() or None

    await db.commit()
    await db.refresh(campaign)

    role = await get_user_campaign_role(db, user_id, campaign_id)
    if role is None:
        raise CampaignServiceError("Campaign not found")

    return CampaignResponse(
        id=str(campaign.id),
        name=campaign.name,
        tone=campaign.tone,
        game_system=campaign.game_system,
        role=role,
    )


async def remove_campaign_member(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    membership = await db.scalar(
        select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == user_id,
        )
    )
    if membership is None:
        raise CampaignServiceError("Member not found")

    if membership.role == "MASTER":
        master_count = await db.scalar(
            select(func.count())
            .select_from(CampaignMember)
            .where(CampaignMember.campaign_id == campaign_id, CampaignMember.role == "MASTER")
        )
        if int(master_count or 0) <= 1:
            raise CampaignServiceError("Cannot remove the only master from the campaign")

    await db.delete(membership)
    await db.commit()


async def delete_campaign(db: AsyncSession, campaign_id: uuid.UUID) -> None:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        raise CampaignServiceError("Campaign not found")

    campaign_id_str = str(campaign_id)
    storage = get_storage_backend()

    docs = (
        await db.scalars(select(CampaignDocument).where(CampaignDocument.campaign_id == campaign_id))
    ).all()
    for doc in docs:
        key = resolve_document_storage_key(doc)
        if storage.exists(key):
            storage.delete_object(key)

    await db.execute(delete(Scene).where(Scene.campaign_id == campaign_id))
    await db.execute(delete(CampaignEntity).where(CampaignEntity.campaign_id == campaign_id))
    await db.execute(delete(CampaignDocument).where(CampaignDocument.campaign_id == campaign_id))
    await db.delete(campaign)
    await db.commit()
    await rag_service.purge_semantic_cache(db, campaign_id=campaign_id_str)

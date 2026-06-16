import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.user import CampaignMember, User
from app.schemas.campaign_mgmt import CampaignCreate, CampaignMemberAdd, CampaignMemberResponse, CampaignResponse


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
        CampaignResponse(id=str(campaign.id), name=campaign.name, tone=campaign.tone, role=role)
        for campaign, role in rows.all()
    ]


async def create_campaign(db: AsyncSession, user_id: uuid.UUID, payload: CampaignCreate) -> CampaignResponse:
    campaign = Campaign(name=payload.name.strip(), tone=payload.tone)
    db.add(campaign)
    await db.flush()

    membership = CampaignMember(campaign_id=campaign.id, user_id=user_id, role="MASTER")
    db.add(membership)
    await db.commit()
    await db.refresh(campaign)

    return CampaignResponse(id=str(campaign.id), name=campaign.name, tone=campaign.tone, role="MASTER")


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

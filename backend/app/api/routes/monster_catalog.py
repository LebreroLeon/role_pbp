import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, parse_uuid, require_campaign_master
from app.core.database import get_db
from app.models.monster_catalog import SystemMonsterCatalog
from app.models.user import User
from app.schemas.monster_catalog import (
    MonsterCatalogDetail,
    MonsterCatalogSummary,
    MonsterSpawnRequest,
    MonsterSpawnResponse,
)
from app.services.monster_spawn import (
    MonsterCatalogError,
    get_catalog_monster,
    search_catalog_monsters,
    spawn_monsters,
)

router = APIRouter(tags=["monster-catalog"])


def _to_summary(entry: SystemMonsterCatalog) -> MonsterCatalogSummary:
    return MonsterCatalogSummary(
        slug=entry.slug,
        name=entry.name,
        challenge_rating=entry.challenge_rating,
        creature_type=entry.creature_type,
        size=entry.size,
        source_document=entry.source_document,
        source_label=entry.source_label,
    )


def _to_detail(entry: SystemMonsterCatalog) -> MonsterCatalogDetail:
    return MonsterCatalogDetail(
        **_to_summary(entry).model_dump(),
        narrative_template=entry.narrative_template,
        sheet_template=entry.sheet_template,
    )


@router.get("/catalog/monsters", response_model=list[MonsterCatalogSummary])
async def list_catalog_monsters(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    system_id: str = Query(default="dnd5e"),
    q: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[MonsterCatalogSummary]:
    _ = current_user
    entries = await search_catalog_monsters(db, system_id=system_id, query=q, limit=limit)
    return [_to_summary(entry) for entry in entries]


@router.get("/catalog/monsters/{slug}", response_model=MonsterCatalogDetail)
async def get_catalog_monster_detail(
    slug: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    system_id: str = Query(default="dnd5e"),
) -> MonsterCatalogDetail:
    _ = current_user
    entry = await get_catalog_monster(db, system_id=system_id, slug=slug)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Monster {slug!r} not found")
    return _to_detail(entry)


@router.post("/campaigns/{campaign_id}/monsters/spawn", response_model=MonsterSpawnResponse)
async def spawn_campaign_monsters(
    campaign_id: str,
    payload: MonsterSpawnRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MonsterSpawnResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_uuid)

    try:
        visibility = payload.player_visibility or ("hidden" if payload.hidden else "visible")
        created = await spawn_monsters(
            db,
            campaign_id=campaign_uuid,
            slug=payload.slug,
            count=payload.count,
            player_visibility=visibility,
            attitude=payload.attitude,
        )
    except MonsterCatalogError as exc:
        status = 404 if "not found" in str(exc).lower() else 422
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    return MonsterSpawnResponse(
        created=[str(entity.id) for entity in created],
        count=len(created),
    )

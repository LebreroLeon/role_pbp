from typing import Annotated

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_system_manual_master
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.system_manual import SystemManualFileStatus, SystemManualStatusResponse
from app.services.system_manuals import (
    build_manual_status_entries,
    fetch_sources_by_system,
    validate_system_id,
)

router = APIRouter(prefix="/system-manuals", tags=["system-manuals"])


@router.get("/{system_id}/status", response_model=SystemManualStatusResponse)
async def get_system_manual_status(
    system_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SystemManualStatusResponse:
    try:
        validate_system_id(system_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await require_system_manual_master(db, current_user, system_id)

    manuals_root = Path(settings.system_manuals_dir)
    sources = await fetch_sources_by_system(db, system_id)
    entries = build_manual_status_entries(
        system_id,
        manuals_root=manuals_root,
        sources_by_filename=sources,
    )

    return SystemManualStatusResponse(
        system_id=system_id,
        files=[SystemManualFileStatus(**entry) for entry in entries],
    )

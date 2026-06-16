from fastapi import APIRouter

from app.schemas.master import MasterAssistRequest, MasterAssistResponse
from app.services.master import build_master_assist_response

router = APIRouter(prefix="/master", tags=["master"])


@router.post("/assist", response_model=MasterAssistResponse)
async def master_assist(payload: MasterAssistRequest) -> MasterAssistResponse:
    return await build_master_assist_response(payload)

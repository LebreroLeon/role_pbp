from datetime import UTC, datetime

from app.schemas.master import MasterAssistRequest, MasterAssistResponse
from app.services.rag import rag_service


async def build_master_assist_response(payload: MasterAssistRequest) -> MasterAssistResponse:
    matches = rag_service.search(
        campaign_id=payload.campaign_id,
        query=payload.query,
        top_k=3,
    )

    context_summary = (
        " | ".join(matches)
        if matches
        else "No indexed campaign memory yet. Scene chat will populate RAG over time."
    )

    suggestions = [
        "Introduce a complication tied to the active scene objective.",
        "Reveal a subtle clue from past events without exposing master secrets.",
        "Shift NPC attitude based on the latest player actions in the buffer.",
    ]

    return MasterAssistResponse(
        query=payload.query,
        context_summary=context_summary,
        suggestions=suggestions,
    )


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()

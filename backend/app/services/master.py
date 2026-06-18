import json
import logging
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignEntity, Scene
from app.schemas.entities import EntityType
from app.schemas.master import MasterAssistRequest, MasterAssistResponse
from app.services.llm import LLMNotConfiguredError, LLMProviderError, chat_completion, parse_json_object
from app.services.rag import rag_service

logger = logging.getLogger(__name__)

SHADOW_MASTER_SYSTEM_PROMPT = """You are the Shadow Master — a private creative assistant for the Game Master (DM) of a tabletop RPG campaign.

You receive context in strict priority order:
1. ABSOLUTE STATE — current entity flags and JSONB documents from the database. If an NPC has is_dead: true or is_present_in_scene: false, they cannot act physically in the present scene.
2. HISTORICAL CONTEXT — semantically retrieved past events (RAG).
3. RECENT CHAT — the live scene message buffer.
4. MASTER QUERY — the DM's question or request.

Rules:
- Ground suggestions in the provided state; do not contradict hard flags.
- Offer actionable narrative, encounter, or pacing ideas for the DM only.
- Never address players directly; this channel is master-only.
- Keep suggestions concise (1-2 sentences each).

Respond ONLY with valid JSON (no markdown fences):
{"context_summary": "<brief synthesis of relevant state and history>", "suggestions": ["<idea 1>", "<idea 2>", "<idea 3>"]}
"""


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def strip_secret_fields_for_llm(data: Any) -> Any:
    """Remove any key starting with secret_ before sending entity context to the LLM (player context)."""
    if isinstance(data, dict):
        return {
            key: strip_secret_fields_for_llm(value)
            for key, value in data.items()
            if not str(key).startswith("secret_")
        }
    if isinstance(data, list):
        return [strip_secret_fields_for_llm(item) for item in data]
    return data


def prepare_entity_document(document: dict, entity_type: EntityType, *, include_secrets: bool) -> dict:
    if include_secrets:
        return deepcopy(document)
    return strip_secret_fields_for_llm(deepcopy(document))


async def fetch_campaign_entities(
    db: AsyncSession,
    campaign_id: uuid.UUID,
) -> list[CampaignEntity]:
    return list(
        await db.scalars(
            select(CampaignEntity)
            .where(CampaignEntity.campaign_id == campaign_id)
            .order_by(CampaignEntity.entity_type, CampaignEntity.created_at)
        )
    )


def build_entity_flags_snapshot(
    entities: list[CampaignEntity],
    *,
    include_secrets: bool,
    focus_entity_id: str | None = None,
) -> list[dict[str, Any]]:
    focus = focus_entity_id.lower() if focus_entity_id else None
    snapshot: list[dict[str, Any]] = []

    for entity in entities:
        entity_id = str(entity.id)
        if focus and entity_id.lower() != focus:
            continue

        try:
            entity_type = EntityType(entity.entity_type)
        except ValueError:
            entity_type = None

        document = entity.document if isinstance(entity.document, dict) else {}
        if entity_type is not None:
            document = prepare_entity_document(document, entity_type, include_secrets=include_secrets)
        elif not include_secrets:
            document = strip_secret_fields_for_llm(document)

        snapshot.append(
            {
                "entity_id": entity_id,
                "entity_type": entity.entity_type,
                "state_flags": document.get("state_flags", {}),
                "document": document,
            }
        )

    return snapshot


def format_chat_buffer(buffer: list, max_size: int) -> list[dict[str, Any]]:
    trimmed = buffer[-max_size:] if max_size > 0 else []
    formatted: list[dict[str, Any]] = []
    for item in trimmed:
        data = item if isinstance(item, dict) else item.model_dump()
        formatted.append(
            {
                "timestamp": data.get("timestamp"),
                "sender_id": data.get("sender_id"),
                "type": data.get("type"),
                "text": data.get("text"),
            }
        )
    return formatted


def build_sandwich_prompt(
    *,
    scene_flags: dict[str, Any],
    scene_context: dict[str, Any],
    entities_snapshot: list[dict[str, Any]],
    rag_chunks: list[str],
    manual_rag_chunks: list[str],
    chat_buffer: list[dict[str, Any]],
    query: str,
) -> str:
    sections = [
        "## ABSOLUTE STATE (Flags & Entities)",
        json.dumps(
            {
                "scene_flags": scene_flags,
                "scene_context": scene_context,
                "entities": entities_snapshot,
            },
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "## HISTORICAL CONTEXT (RAG — Campaign)",
        "\n---\n".join(rag_chunks) if rag_chunks else "(No indexed campaign memory yet.)",
        "",
        "## SYSTEM RULEBOOKS (RAG — Official Manuals)",
        "\n---\n".join(manual_rag_chunks) if manual_rag_chunks else "(No indexed system manuals for this game system.)",
        "",
        "## RECENT CHAT (Buffer)",
        json.dumps(chat_buffer, ensure_ascii=False, indent=2),
        "",
        "## MASTER QUERY",
        query,
    ]
    return "\n".join(sections)


def _fallback_suggestions(query: str) -> list[str]:
    return [
        f"Consider a complication tied to: {query[:120]}",
        "Reveal a subtle clue from past events without exposing master secrets to players.",
        "Shift an NPC attitude based on the latest player actions in the buffer.",
    ]


def _parse_llm_assist_response(raw: str, *, rag_chunks: list[str], query: str) -> tuple[str, list[str]]:
    parsed = parse_json_object(raw)
    if parsed:
        summary = str(parsed.get("context_summary") or "").strip()
        suggestions_raw = parsed.get("suggestions")
        suggestions = (
            [str(item).strip() for item in suggestions_raw if str(item).strip()]
            if isinstance(suggestions_raw, list)
            else []
        )
        if summary and suggestions:
            return summary, suggestions[:5]
        if summary:
            return summary, _fallback_suggestions(query)
        if suggestions:
            fallback_summary = " | ".join(rag_chunks[:3]) if rag_chunks else "Shadow Master analysis ready."
            return fallback_summary, suggestions[:5]

    lines = [line.strip("-• ").strip() for line in raw.splitlines() if line.strip()]
    if lines:
        return lines[0], lines[1:4] or _fallback_suggestions(query)

    fallback_summary = " | ".join(rag_chunks[:3]) if rag_chunks else "No indexed campaign memory yet."
    return fallback_summary, _fallback_suggestions(query)


async def build_master_assist_response(
    db: AsyncSession,
    payload: MasterAssistRequest,
    *,
    scene: Scene,
    top_k: int = 3,
    manual_top_k: int = 2,
) -> MasterAssistResponse:
    from app.services.scenes import load_scene_state

    state = load_scene_state(scene)
    buffer_size = state.memory_settings.max_chat_buffer_size

    campaign = await db.scalar(select(Campaign).where(Campaign.id == scene.campaign_id))
    game_system = campaign.game_system if campaign else None
    if game_system is None:
        logger.warning("Campaign %s has no game_system; skipping system manual RAG", scene.campaign_id)

    rag_chunks = await rag_service.search(
        db,
        campaign_id=payload.campaign_id,
        query=payload.query,
        top_k=top_k,
    )

    manual_rag_chunks: list[str] = []
    if game_system:
        manual_rag_chunks = await rag_service.search_system_manuals(
            db,
            game_system=game_system,
            query=payload.query,
            top_k=manual_top_k,
        )

    entities = await fetch_campaign_entities(db, scene.campaign_id)
    entities_snapshot = build_entity_flags_snapshot(
        entities,
        include_secrets=True,
        focus_entity_id=payload.focus_entity_id,
    )

    chat_buffer = format_chat_buffer(state.chat_buffer, buffer_size)
    user_prompt = build_sandwich_prompt(
        scene_flags=state.state_flags.model_dump(),
        scene_context=state.context.model_dump(),
        entities_snapshot=entities_snapshot,
        rag_chunks=rag_chunks,
        manual_rag_chunks=manual_rag_chunks,
        chat_buffer=chat_buffer,
        query=payload.query,
    )

    all_rag = rag_chunks + manual_rag_chunks
    context_summary = (
        " | ".join(all_rag)
        if all_rag
        else "No indexed campaign memory yet. Scene chat will populate RAG over time."
    )
    suggestions = _fallback_suggestions(payload.query)

    try:
        raw_response = await chat_completion(
            [
                {"role": "system", "content": SHADOW_MASTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        context_summary, suggestions = _parse_llm_assist_response(
            raw_response,
            rag_chunks=rag_chunks,
            query=payload.query,
        )
    except LLMNotConfiguredError as exc:
        return MasterAssistResponse(
            query=payload.query,
            context_summary=context_summary,
            suggestions=suggestions,
            note=str(exc),
        )
    except LLMProviderError as exc:
        logger.error("Shadow Master LLM call failed: %s", exc)
        return MasterAssistResponse(
            query=payload.query,
            context_summary=context_summary,
            suggestions=suggestions,
            note=f"LLM provider error: {exc}",
        )

    return MasterAssistResponse(
        query=payload.query,
        context_summary=context_summary,
        suggestions=suggestions,
    )

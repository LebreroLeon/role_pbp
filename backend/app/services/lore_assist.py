import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignEntity, MemoryDocumentType, Scene
from app.schemas.entities import EntityType
from app.schemas.scene import LoreAssistRequest, LoreAssistResponse
from app.services.entities import find_pc_by_user, strip_master_secrets
from app.services.llm import LLMNotConfiguredError, LLMProviderError, chat_completion
from app.services.master import (
    build_entity_flags_snapshot,
    fetch_campaign_entities,
    format_chat_buffer,
    strip_secret_fields_for_llm,
    utc_now_iso,
)
from app.services.rag import rag_service
from app.services.scenes import SceneServiceError, load_scene_state, save_scene_state

logger = logging.getLogger(__name__)

PLAYER_LORE_SYSTEM_PROMPT = """You are a lore assistant for a tabletop RPG player.

Answer ONLY using the provided context. Never reveal master secrets (fields starting with secret_).
If the character would not know something, say so briefly.
Keep answers concise (2-4 sentences) and in Spanish.

Respond with plain text only (no JSON, no markdown fences)."""


async def build_player_lore_response(
    db: AsyncSession,
    scene: Scene,
    user_id: uuid.UUID,
    payload: LoreAssistRequest,
) -> LoreAssistResponse:
    state = load_scene_state(scene)
    remaining = state.state_flags.remaining_player_lore_tokens
    if remaining <= 0:
        raise SceneServiceError(
            "No quedan consultas de lore en esta escena. Espera al cierre de escena."
        )

    pc = await find_pc_by_user(db, scene.campaign_id, user_id)
    if pc is None:
        raise SceneServiceError("Necesitas un personaje en la campaña para consultar al asistente.")

    campaign = await db.scalar(select(Campaign).where(Campaign.id == scene.campaign_id))
    game_system = campaign.game_system if campaign else None

    query = payload.query.strip()
    if not query:
        raise SceneServiceError("La consulta no puede estar vacía.")

    rag_chunks = await rag_service.search(
        db,
        campaign_id=str(scene.campaign_id),
        query=query,
        top_k=state.memory_settings.rag_top_k_matches,
        include_system_manuals=True,
        game_system=game_system,
    )

    entities = await fetch_campaign_entities(db, scene.campaign_id)
    pc_document = strip_master_secrets(pc.document, EntityType.PC)
    entities_snapshot = build_entity_flags_snapshot(entities, include_secrets=False)
    for entry in entities_snapshot:
        if entry.get("entity_id") == str(pc.id):
            entry["document"] = strip_secret_fields_for_llm(pc_document)

    chat_buffer = format_chat_buffer(state.chat_buffer, state.memory_settings.max_chat_buffer_size)
    user_prompt = "\n".join(
        [
            "## CONTEXTO DE CAMPAÑA (sin secretos)",
            json.dumps(entities_snapshot, ensure_ascii=False, indent=2),
            "",
            "## MEMORIA RECUPERADA",
            "\n---\n".join(rag_chunks) if rag_chunks else "(Sin memoria indexada aún.)",
            "",
            "## CHAT RECIENTE",
            json.dumps(chat_buffer, ensure_ascii=False, indent=2),
            "",
            "## PREGUNTA DEL JUGADOR",
            query,
        ]
    )

    answer = (
        " | ".join(rag_chunks[:2])
        if rag_chunks
        else "No hay suficiente contexto indexado todavía. Pregunta al Máster en el chat."
    )
    note: str | None = None

    try:
        answer = (
            await chat_completion(
                [
                    {"role": "system", "content": PLAYER_LORE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            )
        ).strip()
    except LLMNotConfiguredError as exc:
        note = str(exc)
    except LLMProviderError as exc:
        logger.warning("Player lore assist LLM failed: %s", exc)
        note = "Respuesta generada sin LLM (modo degradado)."

    state.state_flags.remaining_player_lore_tokens = remaining - 1
    save_scene_state(scene, state)
    await db.commit()

    return LoreAssistResponse(
        query=query,
        answer=answer,
        remaining_tokens=state.state_flags.remaining_player_lore_tokens,
        generated_at=utc_now_iso(),
        note=note,
    )

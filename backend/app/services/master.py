import json
import logging
import re
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
- ALWAYS respond in the same language as the MASTER QUERY. If the query is in Spanish, write context_summary and every suggestion entirely in Spanish.

Respond ONLY with valid JSON (no markdown fences):
{"context_summary": "<brief synthesis of relevant state and history>", "suggestions": ["<idea 1>", "<idea 2>", "<idea 3>"]}
"""

SHADOW_MASTER_RULES_SYSTEM_PROMPT = """You are the Shadow Master rules consultant for the Game Master (DM) of a tabletop RPG campaign.

The MASTER QUERY is about game rules, mechanics, equipment, prices, classes, subclasses, spells, proficiencies, or similar — NOT about who is present in the current scene.

Priority order:
1. SYSTEM RULEBOOKS (RAG — Official Manuals) — primary source. Quote or paraphrase retrieved manual text accurately.
2. HISTORICAL CONTEXT — campaign-specific rulings only if manuals are silent.
3. ABSOLUTE STATE / RECENT CHAT — ignore for rules lookups unless the query explicitly names a campaign entity.

Rules:
- Do NOT answer with scene suggestions, NPC ideas, merchant introductions, pacing ideas, or "no such character in scene".
- For price/equipment queries: give item names, costs (gp/po), weight, AC, and restrictions from the manual only — no narrative hooks.
- List proficiencies, features, level requirements, stats, and mechanics from the manual chunks when available.
- If manual chunks are empty or irrelevant, say clearly that no indexed manual passage matched.
- Never address players directly; this channel is master-only.
- ALWAYS respond in the same language as the MASTER QUERY. If the query is in Spanish, write context_summary and every suggestion entirely in Spanish (use "po" for gold pieces when citing prices).

Respond ONLY with valid JSON (no markdown fences):
{"context_summary": "<rules answer grounded in manual chunks>", "suggestions": ["<feature, stat, or price detail>", "<another detail>"]}
"""

RULES_QUERY_PATTERN = re.compile(
    r"(?i)\b("
    r"competenc|proficienc|subclas|subclase|subclass|"
    r"hechiz|spell|clase|class|caracter[ií]stic|feature|"
    r"arquero\s+arcano|arcane\s+archer|"
    r"regla|rules?|mec[aá]nic|mechanic|"
    r"nivel\s+\d|level\s+\d|"
    r"tirada|saving\s+throw|attack\s+roll|"
    r"conjur|cast(?:ing)?|cantrip|truco|"
    r"rasgo|racial|background|transfondo|"
    r"multiclase|multiclass|"
    r"dnd|d&d|5e|5\.?\s*ed|"
    r"precio|precios|price|prices|coste|costos?|costs?|"
    r"cu[aá]nto\s+vale|how\s+much|market|mercado|tienda|shop|"
    r"equipamiento|equipment|equipo|item|objeto|"
    r"armadura|armour|armor|armas?|weapons?"
    r")\b"
)

SPANISH_QUERY_PATTERN = re.compile(
    r"(?i)([áéíóúñü]|"
    r"\b(cu[aá]nto|qu[eé]|c[oó]mo|d[oó]nde|por\s+qu[eé]|"
    r"precio|armadura|competenc|hechiz|subclase|clase|regla|vale|coste|"
    r"equipamiento|caracter[ií]stic|conjur|tirada|nivel|rasgo|transfondo|"
    r"mercado|tienda|objeto|arma|po\b)"
    r")"
)

DND_MANUAL_SEARCH_ALIASES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\barquero\s+arcano\b"), "Arcane Archer"),
    (re.compile(r"(?i)\bluchador\b"), "Fighter"),
    (re.compile(r"(?i)\bcompetencias?\b"), "proficiencies"),
    (re.compile(r"(?i)\bcaracter[ií]sticas?\b"), "features"),
    (re.compile(r"(?i)\bhechizos?\b"), "spells"),
    (re.compile(r"(?i)\bclase\b"), "class"),
    (re.compile(r"(?i)\bsubclase\b"), "subclass"),
    (re.compile(r"(?i)\barmadura\s+pesada(?:\s+completa)?\b"), "heavy armor plate armor equipment price"),
    (re.compile(r"(?i)\barmadura\s+de\s+placas\b"), "plate armor heavy armor"),
    (re.compile(r"(?i)\barmaduras?\b"), "armor equipment"),
    (re.compile(r"(?i)\bequipamiento\b"), "equipment adventuring gear"),
    (re.compile(r"(?i)\bcu[aá]nto\s+vale\b"), "price cost gp gold pieces"),
    (re.compile(r"(?i)\bprecio\b"), "price cost gp"),
    (re.compile(r"(?i)\bmercado\b"), "price shop equipment list"),
]

DEFAULT_MANUAL_TOP_K = 2
RULES_MANUAL_TOP_K = 5


def is_rules_query(query: str) -> bool:
    return bool(RULES_QUERY_PATTERN.search(query.strip()))


def query_language_is_spanish(query: str) -> bool:
    return bool(SPANISH_QUERY_PATTERN.search(query.strip()))


def apply_language_instruction(system_prompt: str, query: str) -> str:
    if not query_language_is_spanish(query):
        return system_prompt
    return (
        f"{system_prompt}\n\n"
        "LANGUAGE (mandatory): The MASTER QUERY is in Spanish. "
        "Write context_summary and every suggestion entirely in Spanish. "
        "Do not use English unless quoting an untranslatable proper noun."
    )


def build_manual_search_query(query: str) -> str:
    """Expand common Spanish D&D terms so manual RAG matches English PDF chunks."""
    expanded = query.strip()
    for pattern, replacement in DND_MANUAL_SEARCH_ALIASES:
        expanded = pattern.sub(replacement, expanded)
    if is_rules_query(query):
        expanded = f"{expanded} official rules manual class subclass features proficiencies"
    return expanded


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
    rules_query: bool = False,
) -> str:
    if rules_query:
        sections = [
            "## SYSTEM RULEBOOKS (RAG — Official Manuals) [PRIMARY FOR THIS QUERY]",
            "\n---\n".join(manual_rag_chunks) if manual_rag_chunks else "(No indexed system manuals for this game system.)",
            "",
            "## HISTORICAL CONTEXT (RAG — Campaign)",
            "\n---\n".join(rag_chunks) if rag_chunks else "(No indexed campaign memory yet.)",
            "",
            "## ABSOLUTE STATE (Flags & Entities — secondary for rules lookups)",
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
            "## RECENT CHAT (Buffer)",
            json.dumps(chat_buffer, ensure_ascii=False, indent=2),
            "",
            "## MASTER QUERY (rules / mechanics)",
            query,
        ]
        return "\n".join(sections)

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


def _fallback_suggestions(query: str, *, rules_query: bool = False) -> list[str]:
    if rules_query:
        return [
            "Revisa los fragmentos del manual indexado en context_summary.",
            "Si no hay pasaje relevante, indica al Máster que indexe el PHB o manual de tiendas.",
        ]
    return [
        f"Consider a complication tied to: {query[:120]}",
        "Reveal a subtle clue from past events without exposing master secrets to players.",
        "Shift an NPC attitude based on the latest player actions in the buffer.",
    ]


def _parse_llm_assist_response(
    raw: str,
    *,
    rag_chunks: list[str],
    manual_rag_chunks: list[str],
    query: str,
    rules_query: bool = False,
) -> tuple[str, list[str]]:
    all_rag = rag_chunks + manual_rag_chunks
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
            return summary, _fallback_suggestions(query, rules_query=rules_query)
        if suggestions:
            fallback_summary = " | ".join(all_rag[:3]) if all_rag else "Shadow Master analysis ready."
            return fallback_summary, suggestions[:5]

    lines = [line.strip("-• ").strip() for line in raw.splitlines() if line.strip()]
    if lines:
        return lines[0], lines[1:4] or _fallback_suggestions(query, rules_query=rules_query)

    fallback_summary = " | ".join(all_rag[:3]) if all_rag else "No indexed campaign memory yet."
    return fallback_summary, _fallback_suggestions(query, rules_query=rules_query)


async def build_master_assist_response(
    db: AsyncSession,
    payload: MasterAssistRequest,
    *,
    scene: Scene,
    top_k: int = 3,
    manual_top_k: int = DEFAULT_MANUAL_TOP_K,
) -> MasterAssistResponse:
    from app.services.scenes import load_scene_state

    state = load_scene_state(scene)
    buffer_size = state.memory_settings.max_chat_buffer_size
    rules_query = is_rules_query(payload.query)
    effective_manual_top_k = RULES_MANUAL_TOP_K if rules_query else manual_top_k

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
        manual_search_query = build_manual_search_query(payload.query) if rules_query else payload.query
        manual_rag_chunks = await rag_service.search_system_manuals(
            db,
            game_system=game_system,
            query=manual_search_query,
            top_k=effective_manual_top_k,
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
        rules_query=rules_query,
    )

    all_rag = rag_chunks + manual_rag_chunks
    if rules_query and manual_rag_chunks:
        context_summary = " | ".join(manual_rag_chunks[:3])
        suggestions = manual_rag_chunks[:5]
    elif all_rag:
        context_summary = " | ".join(all_rag)
        suggestions = _fallback_suggestions(payload.query, rules_query=rules_query)
    else:
        context_summary = "No indexed campaign memory yet. Scene chat will populate RAG over time."
        suggestions = _fallback_suggestions(payload.query, rules_query=rules_query)

    base_system_prompt = SHADOW_MASTER_RULES_SYSTEM_PROMPT if rules_query else SHADOW_MASTER_SYSTEM_PROMPT
    system_prompt = apply_language_instruction(base_system_prompt, payload.query)

    try:
        raw_response = await chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        context_summary, suggestions = _parse_llm_assist_response(
            raw_response,
            rag_chunks=rag_chunks,
            manual_rag_chunks=manual_rag_chunks,
            query=payload.query,
            rules_query=rules_query,
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

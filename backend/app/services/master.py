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
- context_summary: brief synthesis for the DM — analysis, rationale, or pacing notes (this field may address the DM).
- suggestions: actionable narrative, encounter, or pacing ideas. Keep each item concise (1-2 sentences) unless NARRATIVE MODE applies.
- Never address players directly in context_summary; this channel is master-only.
- ALWAYS respond in the same language as the MASTER QUERY. If the query is in Spanish, write context_summary and every suggestion entirely in Spanish.

Respond ONLY with valid JSON (no markdown fences):
{"context_summary": "<brief synthesis of relevant state and history>", "suggestions": ["<idea 1>", "<idea 2>", "<idea 3>"]}
"""

SHADOW_MASTER_NARRATIVE_MODE_APPENDIX = """
NARRATIVE MODE (mandatory for this query):
- The MASTER QUERY asks for spoken narration, scene openings, descriptions, atmosphere, or prose the players will read in chat.

Campaign grounding (mandatory — never write generic disconnected prose):
- Every narrative suggestion MUST be anchored in the provided context: ABSOLUTE STATE (scene flags, entities, JSONB documents), HISTORICAL CONTEXT (campaign RAG), RECENT CHAT, and closed-scene summaries when present.
- Do NOT invent plot beats, locations, NPCs, factions, or items that are not supported by that context. Generic sensory atmosphere (weather, silence, tension) is allowed only when it fits the established scene and does not contradict known facts.
- When context names concrete campaign elements (e.g. Prólogo, bosque, Arturo, a prior ambush, a known location), weave those names and facts into the prose — do not substitute unrelated placeholders.
- Respect hard entity flags: dead or absent NPCs cannot act physically; present entities and scene objectives should inform what the narration describes.

context_summary (DM-facing):
- Brief analysis of why these options fit the scene AND which lore/context elements each suggestion draws from (e.g. "Suggestion 1 uses the forest ambush RAG + Arturo's wounded state; Suggestion 2 echoes the Prólogo hook from chat.").
- If campaign memory is thin, say what is missing; do not fabricate lore to fill gaps.

suggestions:
- Each item MUST be copy-paste ready narrator text — vivid, descriptive prose in professional novel tone (first-person narrator or omniscient voice). Write 2-4 sentences per suggestion that the DM publishes directly in the scene chat.
- Ground every suggestion in retrieved campaign/scene context; avoid stock fantasy filler unrelated to this campaign.
- FORBIDDEN in suggestions: meta or coaching phrasing such as "El maestro podría...", "Podrías narrar...", "Consider describing...", "The GM could...", "You could start by...". No instructions to the DM inside suggestions — only the in-world narration itself.
- Example BAD suggestion: "El maestro puede comenzar describiendo el silencio del claro."
- Example GOOD suggestion (when forest + ambush are in context): "El silencio cae sobre el claro como un sudario húmedo. Desde el centro, un susurro en lengua desconocida raspa la garganta del bosque..."
"""

SHADOW_MASTER_CAMPAIGN_SYSTEM_PROMPT = """You are the Shadow Master campaign memory consultant for the Game Master (DM) of a tabletop RPG campaign.

The MASTER QUERY is about lore, campaign history, what happened before, scene context, NPCs, locations, relationships, or facts grounded in this campaign — NOT game rules from rulebooks.

Priority order:
1. ABSOLUTE STATE — current entity flags, JSONB documents, and scene context from the database.
2. HISTORICAL CONTEXT — semantically retrieved campaign memory (RAG).
3. RECENT CHAT — the live scene message buffer.
4. SYSTEM RULEBOOKS — ignore unless the query explicitly asks for rules.

Rules:
- Ground answers in retrieved campaign memory and entity state; do not invent plot details unsupported by context.
- Do NOT answer with rulebook mechanics, prices, class features, or official manual text unless the query explicitly asks for rules.
- Do NOT output narrator prose for players unless the MASTER QUERY explicitly asks for narration or scene description to publish.
- context_summary: synthesis of relevant campaign and scene facts for the DM.
- suggestions: actionable DM notes — reminders, connections, contradictions to watch, entity facts, follow-up angles. Keep each item concise (1-2 sentences). Do NOT use meta coaching such as "El maestro podría...", "Podrías narrar...", or invented pacing ideas without grounding in provided context.
- If campaign memory is empty, say clearly what is missing; do not fabricate lore.
- Never address players directly; this channel is master-only.
- ALWAYS respond in the same language as the MASTER QUERY. If the query is in Spanish, write context_summary and every suggestion entirely in Spanish.

Respond ONLY with valid JSON (no markdown fences):
{"context_summary": "<campaign/scene synthesis>", "suggestions": ["<useful fact or follow-up>", "<another detail>"]}
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

NARRATIVE_QUERY_PATTERN = re.compile(
    r"(?i)\b("
    r"narraci[oó]n|narrativ|narrar|narrador|narrator|"
    r"empezar|comenzar|iniciar|arrancar|continuar|seguir|opening|"
    r"historia|story|"
    r"describ|descripci[oó]n|describe|"
    r"atm[oó]sfera|ambiente|tone|tono|"
    r"escena\s+actual|current\s+scene|"
    r"tercera\s+escena|third\s+scene|"
    r"prosa|hook|apertura|introduc|"
    r"m[aá]ndalo|mandalo|"
    r"escribe\s+como"
    r")\b"
)

NARRATOR_PROSE_REQUEST_PATTERN = re.compile(
    r"(?i)("
    r"como\s+si\s+fueras\s+(?:el\s+)?(?:m[aá]ster|master|dm|gm|narrador|narrator)|"
    r"(?:m[aá]ndalo|mandalo|env[ií]alo|escr[ií]belo)\s+(?:como\s+)?"
    r"(?:si\s+fueras\s+)?(?:el\s+)?(?:m[aá]ster|master|dm|gm|narrador|narrator)?|"
    r"escribe\s+como\s+(?:el\s+)?(?:m[aá]ster|master|dm|gm|narrador|narrator)|"
    r"(?:como|as\s+if\s+you\s+(?:were|are))\s+(?:the\s+)?(?:gm|dm|master|narrator)|"
    r"write\s+(?:it\s+)?as\s+(?:the\s+)?(?:gm|dm|master|narrator)"
    r")"
)

CREATIVE_META_PATTERN = re.compile(
    r"(?i)\b("
    r"complicaci[oó]n|complication|"
    r"qu[eé]\s+(?:complicaci[oó]n|idea|twist|giro)|"
    r"encaja\s+con|what\s+fits|"
    r"brainstorm|lluvia\s+de\s+ideas"
    r")\b"
)

NARRATIVE_META_PREFIX = re.compile(
    r"(?i)^("
    r"el\s+(?:maestro|master|dm|gm|director)\s+(?:podr[ií]a|puede|deber[ií]a|could|can|might)|"
    r"podr[ií]as\s+(?:narrar|empezar|comenzar|describir|iniciar)|"
    r"you\s+could\s+(?:narrate|describe|start|begin|open)|"
    r"the\s+(?:gm|dm|master)\s+(?:could|can|might)|"
    r"(?:consider|try)\s+(?:describing|narrating|starting|opening)|"
    r"comienza\s+describiendo|"
    r"el\s+narrador\s+podr[ií]a|"
    r"start\s+by\s+describing"
    r")[\s,:—\-]*"
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


def asks_for_narrator_prose(query: str) -> bool:
    return bool(NARRATOR_PROSE_REQUEST_PATTERN.search(query.strip()))


def is_creative_meta_query(query: str) -> bool:
    q = query.strip()
    if not CREATIVE_META_PATTERN.search(q):
        return False
    return not asks_for_narrator_prose(q)


def is_narrative_query(query: str) -> bool:
    q = query.strip()
    if asks_for_narrator_prose(q):
        return True
    if is_creative_meta_query(q):
        return False
    return bool(NARRATIVE_QUERY_PATTERN.search(q))


def resolve_query_kind(query: str) -> str:
    if is_rules_query(query):
        return "rules"
    if is_narrative_query(query):
        return "narrative"
    return "creative"


def sanitize_narrative_suggestion(text: str) -> str:
    cleaned = NARRATIVE_META_PREFIX.sub("", text.strip()).strip()
    return cleaned or text.strip()


def sanitize_narrative_suggestions(suggestions: list[str]) -> list[str]:
    return [sanitize_narrative_suggestion(item) for item in suggestions if item.strip()]


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


def resolve_effective_mode(query: str, mode: str | None = None) -> str:
    """Return narrative | rules | campaign | creative."""
    if mode in ("narrative", "rules", "campaign"):
        return mode
    return resolve_query_kind(query)


def build_shadow_master_system_prompt(query: str, mode: str | None = None) -> tuple[str, str]:
    """Return (system_prompt, query_kind)."""
    effective_mode = resolve_effective_mode(query, mode)
    if effective_mode == "rules":
        base = SHADOW_MASTER_RULES_SYSTEM_PROMPT
    elif effective_mode == "campaign":
        base = SHADOW_MASTER_CAMPAIGN_SYSTEM_PROMPT
    else:
        base = SHADOW_MASTER_SYSTEM_PROMPT
        if effective_mode == "narrative":
            base = f"{base}\n{SHADOW_MASTER_NARRATIVE_MODE_APPENDIX}"
    return apply_language_instruction(base, query), effective_mode


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


def build_campaign_context_snapshot(
    campaign: Campaign | None,
    arc_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Campaign-level style and macro-plot fields for Shadow Master grounding."""
    if campaign is None:
        return {}

    plot_line: dict[str, Any] = {}
    if isinstance(arc_manifest, dict):
        raw_plot = arc_manifest.get("plot_line")
        if isinstance(raw_plot, dict):
            plot_line = raw_plot

    context: dict[str, Any] = {
        "campaign_name": campaign.name,
        "campaign_tone": campaign.tone,
        "game_system": campaign.game_system,
    }
    if plot_line:
        for key in ("title", "narrative_tone", "global_summary", "current_act"):
            value = plot_line.get(key)
            if value is not None and value != "":
                context[f"arc_{key}"] = value
    return context


def format_campaign_context_section(campaign_context: dict[str, Any]) -> str | None:
    if not campaign_context:
        return None
    return json.dumps(campaign_context, ensure_ascii=False, indent=2)


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
    campaign_context: dict[str, Any] | None = None,
    rules_query: bool = False,
    campaign_query: bool = False,
    narrative_query: bool = False,
) -> str:
    campaign_profile = format_campaign_context_section(campaign_context or {})
    campaign_profile_block: list[str] = []
    if campaign_profile:
        campaign_profile_block = [
            "## CAMPAIGN PROFILE (name, tone, arc) [style and macro-plot grounding]",
            campaign_profile,
            "",
        ]
    if campaign_query or narrative_query:
        manual_label = (
            "## SYSTEM RULEBOOKS (RAG — Official Manuals) "
            "[secondary — atmosphere/setting tone only; ignore mechanics unless query asks for rules]"
            if narrative_query
            else "## SYSTEM RULEBOOKS (RAG — Official Manuals) "
            "[secondary — ignore unless query asks for rules]"
        )
        query_label = (
            "## MASTER QUERY (narrative / scene description)"
            if narrative_query
            else "## MASTER QUERY (campaign / scene / lore)"
        )
        sections = [
            *campaign_profile_block,
            "## ABSOLUTE STATE (Flags & Entities) [PRIMARY FOR THIS QUERY]",
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
            "## HISTORICAL CONTEXT (RAG — Campaign) [PRIMARY FOR THIS QUERY]",
            "\n---\n".join(rag_chunks) if rag_chunks else "(No indexed campaign memory yet.)",
            "",
            "## RECENT CHAT (Buffer) [PRIMARY FOR THIS QUERY]",
            json.dumps(chat_buffer, ensure_ascii=False, indent=2),
            "",
            manual_label,
            "\n---\n".join(manual_rag_chunks) if manual_rag_chunks else "(Not prioritized for campaign/scene queries.)",
            "",
            query_label,
            query,
        ]
        return "\n".join(sections)

    if rules_query:
        sections = [
            *campaign_profile_block,
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
        *campaign_profile_block,
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


_SUGGESTION_JSON_KEYS = (
    "suggestions",
    "bullet_points",
    "sugerencias",
    "ideas",
    "narrative_suggestions",
    "opciones",
)


def _coerce_suggestion_list(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str) and raw.strip():
        lines = [line.strip("-• ").strip() for line in raw.splitlines() if line.strip()]
        return lines or [raw.strip()]
    return []


def _extract_suggestions_from_parsed(parsed: dict[str, Any]) -> list[str]:
    for key in _SUGGESTION_JSON_KEYS:
        items = _coerce_suggestion_list(parsed.get(key))
        if items:
            return items
    return []


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
    narrative_query: bool = False,
) -> tuple[str, list[str]]:
    all_rag = rag_chunks + manual_rag_chunks
    parsed = parse_json_object(raw)
    if parsed:
        summary = str(
            parsed.get("context_summary")
            or parsed.get("summary")
            or parsed.get("analisis")
            or parsed.get("analysis")
            or ""
        ).strip()
        suggestions = _extract_suggestions_from_parsed(parsed)
        if narrative_query and suggestions:
            suggestions = sanitize_narrative_suggestions(suggestions)
        if narrative_query and not suggestions and summary:
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n", summary) if part.strip()]
            if len(paragraphs) >= 2:
                suggestions = sanitize_narrative_suggestions(paragraphs[1:4])
        if summary and suggestions:
            return summary, suggestions[:5]
        if summary:
            return summary, _fallback_suggestions(query, rules_query=rules_query)
        if suggestions:
            fallback_summary = " | ".join(all_rag[:3]) if all_rag else "Shadow Master analysis ready."
            return fallback_summary, suggestions[:5]

    lines = [line.strip("-• ").strip() for line in raw.splitlines() if line.strip()]
    if lines:
        suggestions = lines[1:4] or _fallback_suggestions(query, rules_query=rules_query)
        if narrative_query:
            suggestions = sanitize_narrative_suggestions(suggestions)
        return lines[0], suggestions

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
    effective_mode = resolve_effective_mode(payload.query, payload.mode)
    rules_query = effective_mode == "rules"
    narrative_query = effective_mode == "narrative"
    campaign_query = effective_mode == "campaign"
    query_kind = effective_mode
    effective_manual_top_k = (
        RULES_MANUAL_TOP_K
        if rules_query
        else (0 if campaign_query or narrative_query else manual_top_k)
    )

    campaign = await db.scalar(select(Campaign).where(Campaign.id == scene.campaign_id))
    game_system = campaign.game_system if campaign else None
    if game_system is None:
        logger.warning("Campaign %s has no game_system; skipping system manual RAG", scene.campaign_id)

    arc_entity = await db.scalar(
        select(CampaignEntity).where(
            CampaignEntity.campaign_id == scene.campaign_id,
            CampaignEntity.entity_type == EntityType.ARC_MANIFEST.value,
        )
    )
    arc_manifest: dict[str, Any] | None = None
    if arc_entity is not None:
        arc_doc = getattr(arc_entity, "document", None)
        if isinstance(arc_doc, dict):
            arc_manifest = dict(arc_doc)
    campaign_context = build_campaign_context_snapshot(campaign, arc_manifest)

    rag_chunks = await rag_service.search(
        db,
        campaign_id=payload.campaign_id,
        query=payload.query,
        top_k=top_k,
    )

    manual_rag_chunks: list[str] = []
    if game_system and effective_manual_top_k > 0:
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
        campaign_context=campaign_context,
        rules_query=rules_query,
        campaign_query=campaign_query,
        narrative_query=narrative_query,
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

    system_prompt, query_kind = build_shadow_master_system_prompt(payload.query, payload.mode)

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
            narrative_query=narrative_query,
        )
    except LLMNotConfiguredError as exc:
        return MasterAssistResponse(
            query=payload.query,
            context_summary=context_summary,
            suggestions=suggestions,
            query_kind=query_kind,
            note=str(exc),
        )
    except LLMProviderError as exc:
        logger.error("Shadow Master LLM call failed: %s", exc)
        return MasterAssistResponse(
            query=payload.query,
            context_summary=context_summary,
            suggestions=suggestions,
            query_kind=query_kind,
            note=f"LLM provider error: {exc}",
        )

    return MasterAssistResponse(
        query=payload.query,
        context_summary=context_summary,
        suggestions=suggestions,
        query_kind=query_kind,
    )

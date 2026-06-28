import uuid
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignEntity, CampaignMemory, MemoryDocumentType, Scene, SceneMessage, SceneMessageLike
from app.services.chat_message_images import ChatMessageImageError, validate_message_image_url
from app.schemas.scene import (
    ChatMessage,
    CloseSceneResponse,
    CombatState,
    DEFAULT_MAX_CHAT_BUFFER_SIZE,
    DiceRollRequest,
    InitiativeEntry,
    LEGACY_MAX_CHAT_BUFFER_SIZE,
    MasterBriefingLocation,
    MasterBriefingNpcEntry,
    MasterBriefingOpenScene,
    MasterBriefingResponse,
    MemorySettings,
    NpcPresenceEntry,
    PostMessageRequest,
    PreparedEntityRef,
    SceneContext,
    SceneCreate,
    SceneMetadata,
    ScenePickerItem,
    ScenePresenceUpdate,
    ScenePrepUpdate,
    SceneResponse,
    SceneScratchpadUpdate,
    SceneState,
    SceneStatusType,
    SceneTurnManagementUpdate,
    StateFlags,
    TurnManagement,
)
from app.services.dice import (
    build_generic_roll_details,
    format_raw_roll_summary,
    roll_dice as roll_dice_expression,
)
from app.services.message_likes import delete_likes_for_message, fetch_likes_by_message_id, toggle_message_like
from app.services.scene_messages import (
    delete_persisted_scene_message,
    list_all_scene_messages,
    persist_scene_message,
    update_persisted_read_by,
)
from app.services.combat_resolver import entity_display_name
from app.services.entities import CharacterSheetError, find_pc_by_user, get_campaign_or_error
from app.services.llm import LLMError, LLMNotConfiguredError, chat_completion
from app.services.master import utc_now_iso
from app.services.pbp_turn import (
    PbpTurnError,
    advance_pbp_turn,
    assert_pbp_post_allowed,
    ensure_pbp_initiative_order,
    fetch_entities_by_id,
    is_pbp_enforcement_active,
    sort_initiative_entries,
    sync_turn_management_from_initiative,
)
from app.services.rag import rag_service

ALLOWED_MESSAGE_TYPES = {"SPEAK", "ACTION", "CONTEXT", "MASTER", "NARRATIVE", "DICE_ROLL"}
NARRATIVE_MESSAGE_TYPES = {"SPEAK", "ACTION", "CONTEXT", "MASTER", "NARRATIVE"}
ALLOWED_SPEAKER_TYPES = {"MASTER", "NPC", "PC", "NARRATOR"}
DEFAULT_NARRATOR_DISPLAY_NAME = "Máster / Narrador"
MASTER_DICE_ROLL_DISPLAY_NAME = "Máster"
INTERACTIVE_SCENE_STATUSES = {"ACTIVE"}
FROZEN_SCENE_DETAIL = "La escena está congelada por el Máster."
OPEN_SCENE_BLOCK_MESSAGE = (
    "Hay una escena abierta (activa o pausada). Ciérrala antes de activar otra."
)
AUTO_CLOSED_SCENE_NOTE = "Cerrada automáticamente al abrir otra escena."
FALLBACK_SUMMARY_MESSAGE_COUNT = 5


class SceneServiceError(ValueError):
    pass


def normalize_message_type(message_type: str) -> str:
    normalized = message_type.upper()
    if normalized == "NARRATIVE":
        return "ACTION"
    if normalized not in ALLOWED_MESSAGE_TYPES:
        raise SceneServiceError(f"Invalid message type: {message_type}")
    return normalized


def normalize_chat_buffer(buffer: list) -> list[dict]:
    normalized: list[dict] = []
    for index, item in enumerate(buffer):
        data = item if isinstance(item, dict) else item.model_dump()
        entry = dict(data)
        if not entry.get("id"):
            entry["id"] = f"legacy-{index}-{entry.get('timestamp', '')}"
        entry["read_by"] = list(entry.get("read_by") or [])
        if entry.get("type") == "NARRATIVE":
            entry["type"] = "ACTION"
        if not entry.get("visibility"):
            entry["visibility"] = "all"
        normalized.append(entry)
    return normalized


def is_flat_scene_state(data: dict) -> bool:
    return "metadata" not in data and "campaign_id" in data


def _coerce_memory_settings(raw: object) -> dict:
    if isinstance(raw, dict):
        max_chat_buffer_size = raw.get("max_chat_buffer_size", DEFAULT_MAX_CHAT_BUFFER_SIZE)
        if max_chat_buffer_size == LEGACY_MAX_CHAT_BUFFER_SIZE:
            max_chat_buffer_size = DEFAULT_MAX_CHAT_BUFFER_SIZE
        return {
            "max_chat_buffer_size": max_chat_buffer_size,
            "rag_top_k_matches": raw.get("rag_top_k_matches", 3),
            "max_player_lore_queries_per_scene": raw.get("max_player_lore_queries_per_scene", 3),
        }
    return MemorySettings().model_dump()


def _coerce_state_flags(raw: object) -> dict:
    if isinstance(raw, dict):
        return {
            "conflict_mode_active": bool(raw.get("conflict_mode_active", False)),
            "ai_alert_triggered": bool(raw.get("ai_alert_triggered", False)),
            "remaining_player_lore_tokens": raw.get("remaining_player_lore_tokens", 3),
        }
    return StateFlags().model_dump()


def _coerce_turn_management(raw: object) -> dict:
    if isinstance(raw, dict):
        return {
            "current_turn_player_id": raw.get("current_turn_player_id"),
            "turn_order": list(raw.get("turn_order") or []),
            "pbp_enabled": bool(raw.get("pbp_enabled", False)),
            "order_source": raw.get("order_source", "manual"),
        }
    return TurnManagement().model_dump()


def _coerce_initiative_order(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    entries: list[dict] = []
    for item in raw:
        if isinstance(item, str):
            entries.append({"entity_id": item})
            continue
        if isinstance(item, dict) and item.get("entity_id"):
            entries.append(dict(item))
    return entries


def _coerce_combat(raw: object, state_flags: dict) -> dict:
    if not isinstance(raw, dict):
        conflict_active = bool(state_flags.get("conflict_mode_active", False))
        return CombatState(conflict_mode_active=conflict_active, is_active=conflict_active).model_dump()

    conflict_active = bool(raw.get("conflict_mode_active", state_flags.get("conflict_mode_active", False)))
    is_active = bool(raw.get("is_active", conflict_active))
    return {
        "is_active": is_active,
        "round": int(raw.get("round", 0)),
        "initiative_order": _coerce_initiative_order(raw.get("initiative_order", [])),
        "current_turn_entity_id": raw.get("current_turn_entity_id"),
        "conflict_mode_active": conflict_active,
    }


def migrate_scene_state(data: dict, *, scene_status: str | None = None) -> dict:
    if not is_flat_scene_state(data):
        migrated = dict(data)
        state_flags = _coerce_state_flags(migrated.get("state_flags"))
        migrated["state_flags"] = state_flags
        migrated["combat"] = _coerce_combat(migrated.get("combat"), state_flags)
        migrated["turn_management"] = _coerce_turn_management(migrated.get("turn_management"))
        if scene_status is not None and isinstance(migrated.get("metadata"), dict):
            migrated["metadata"]["status"] = scene_status
        context = migrated.get("context")
        if isinstance(context, dict):
            if "hidden_npc_ids" not in context:
                context["hidden_npc_ids"] = []
            context.setdefault("master_prep_notes", None)
            context.setdefault("master_scene_scratchpad", None)
            context.setdefault("opening_narration", None)
            context.setdefault("prepared_entity_refs", [])
        migrated["memory_settings"] = _coerce_memory_settings(migrated.get("memory_settings"))
        return migrated

    memory_settings = _coerce_memory_settings(data.get("memory_settings"))
    state_flags = _coerce_state_flags(data.get("state_flags"))
    status = scene_status or data.get("status", "ACTIVE")

    return {
        "metadata": {
            "campaign_id": data.get("campaign_id", ""),
            "status": status,
        },
        "context": {
            "location_id": data.get("location_id"),
            "active_npc_ids": list(data.get("active_npc_ids") or []),
            "hidden_npc_ids": list(data.get("hidden_npc_ids") or []),
            "scene_objective": data.get("scene_objective"),
            "master_prep_notes": data.get("master_prep_notes"),
            "master_scene_scratchpad": data.get("master_scene_scratchpad"),
            "opening_narration": data.get("opening_narration"),
            "prepared_entity_refs": list(data.get("prepared_entity_refs") or []),
        },
        "turn_management": _coerce_turn_management(
            {
                "current_turn_player_id": data.get("current_turn_player_id"),
                "turn_order": list(data.get("turn_order") or []),
            }
        ),
        "memory_settings": memory_settings,
        "chat_buffer": data.get("chat_buffer", []),
        "state_flags": state_flags,
        "combat": _coerce_combat(data.get("combat"), state_flags),
    }


def load_scene_state(scene: Scene) -> SceneState:
    state_data = migrate_scene_state(dict(scene.scene_state), scene_status=scene.status)
    state_data["chat_buffer"] = normalize_chat_buffer(state_data.get("chat_buffer", []))
    return SceneState.model_validate(state_data)


def save_scene_state(scene: Scene, state: SceneState) -> None:
    scene.scene_state = state.model_dump()
    scene.status = state.metadata.status


def ensure_scene_post_allowed(scene: Scene, *, sender_role: str = "PLAYER") -> None:
    """ACTIVE allows everyone; PAUSED blocks players but not the Master."""
    status = scene.status
    if status in INTERACTIVE_SCENE_STATUSES:
        return
    if status == "PAUSED" and sender_role == "MASTER":
        return
    if status == "PAUSED":
        raise SceneServiceError(FROZEN_SCENE_DETAIL)
    raise SceneServiceError(f"Scene is {status}")


def _speaker_fields_requested(payload: PostMessageRequest) -> bool:
    return any(
        value is not None and str(value).strip()
        for value in (
            payload.speaker_entity_id,
            payload.speaker_display_name,
            payload.speaker_type,
        )
    )


async def resolve_message_speaker_fields(
    db: AsyncSession,
    scene: Scene,
    payload: PostMessageRequest,
    *,
    sender_id: str,
    sender_role: str,
    msg_type: str,
) -> dict[str, str | None]:
    if msg_type not in NARRATIVE_MESSAGE_TYPES:
        if _speaker_fields_requested(payload):
            raise SceneServiceError("Speaker identity not allowed for this message type")
        return {}

    if sender_role != "MASTER":
        if _speaker_fields_requested(payload):
            raise SceneServiceError("Only MASTER can set speaker identity")
        try:
            user_uuid = uuid.UUID(str(sender_id))
        except ValueError:
            return {}
        pc = await find_pc_by_user(db, scene.campaign_id, user_uuid)
        if pc is None:
            return {}
        return {
            "speaker_type": "PC",
            "speaker_display_name": entity_display_name(pc),
            "speaker_entity_id": str(pc.id),
        }

    speaker_type = (payload.speaker_type or "NARRATOR").upper()
    if speaker_type not in ALLOWED_SPEAKER_TYPES:
        raise SceneServiceError(f"Invalid speaker type: {speaker_type}")

    if speaker_type in {"NARRATOR", "MASTER"}:
        return {
            "speaker_type": speaker_type,
            "speaker_display_name": DEFAULT_NARRATOR_DISPLAY_NAME,
            "speaker_entity_id": None,
        }

    entity_id = payload.speaker_entity_id
    if not entity_id:
        raise SceneServiceError("speaker_entity_id required for NPC/PC speaker")

    try:
        entity_uuid = uuid.UUID(str(entity_id))
    except ValueError as exc:
        raise SceneServiceError("Invalid speaker_entity_id") from exc

    entity = await db.scalar(
        select(CampaignEntity).where(
            CampaignEntity.campaign_id == scene.campaign_id,
            CampaignEntity.id == entity_uuid,
        )
    )
    if entity is None:
        raise SceneServiceError("Speaker entity not found in campaign")
    if entity.entity_type != speaker_type:
        raise SceneServiceError(
            f"Entity type mismatch: expected {speaker_type}, got {entity.entity_type}"
        )

    display_name = payload.speaker_display_name
    if not isinstance(display_name, str) or not display_name.strip():
        display_name = entity_display_name(entity)

    return {
        "speaker_type": speaker_type,
        "speaker_display_name": display_name.strip(),
        "speaker_entity_id": str(entity.id),
    }


def get_combat_state(state: SceneState) -> CombatState:
    return state.combat


def set_initiative_order(state: SceneState, entries: list[InitiativeEntry]) -> None:
    state.combat.initiative_order = entries
    if entries and state.combat.current_turn_entity_id is None:
        state.combat.current_turn_entity_id = entries[0].entity_id


def set_combat_active(state: SceneState, active: bool) -> None:
    state.combat.is_active = active
    state.combat.conflict_mode_active = active
    state.state_flags.conflict_mode_active = active
    if not active:
        state.combat.current_turn_entity_id = None


def set_combat_round(state: SceneState, round_number: int) -> None:
    state.combat.round = max(0, round_number)


def set_current_turn_entity(state: SceneState, entity_id: str | None) -> None:
    state.combat.current_turn_entity_id = entity_id


def default_scene_state(
    campaign_id: str,
    *,
    turn_order: list[str],
    scene_objective: str | None = None,
    location_id: str | None = None,
    opening_narration: str | None = None,
    master_prep_notes: str | None = None,
    prepared_entity_refs: list[PreparedEntityRef] | None = None,
    status: SceneStatusType = "ACTIVE",
) -> SceneState:
    return SceneState(
        metadata=SceneMetadata(campaign_id=str(campaign_id), status=status),
        context=SceneContext(
            scene_objective=scene_objective,
            location_id=location_id,
            opening_narration=opening_narration,
            master_prep_notes=master_prep_notes,
            prepared_entity_refs=list(prepared_entity_refs or []),
        ),
        turn_management=TurnManagement(
            turn_order=turn_order,
            current_turn_player_id=turn_order[0] if turn_order else None,
        ),
    )


def scene_to_response(scene: Scene, *, viewer_role: str = "MASTER") -> SceneResponse:
    state = load_scene_state(scene)
    state = filter_scene_state_for_viewer(state, viewer_role)
    summary = state.metadata.closure_summary if scene.status == "CLOSED" else None
    return SceneResponse(
        id=str(scene.id),
        campaign_id=str(scene.campaign_id),
        scene_number=scene.scene_number,
        display_name=scene.display_name,
        status=scene.status,
        summary=summary,
        scene_state=state,
    )


def _strip_master_only_scene_context(context: SceneContext) -> None:
    context.scene_objective = None
    context.master_prep_notes = None
    context.master_scene_scratchpad = None
    context.opening_narration = None
    context.prepared_entity_refs = []
    context.location_id = None


def filter_scene_state_for_viewer(state: SceneState, viewer_role: str) -> SceneState:
    if viewer_role == "MASTER":
        return state
    filtered = state.model_copy(deep=True)
    filtered.chat_buffer = [
        message
        for message in filtered.chat_buffer
        if (message.visibility or "all") != "master_only"
    ]
    _strip_master_only_scene_context(filtered.context)
    return filtered


def apply_likes_to_scene_state(state: SceneState, likes_by_message_id: dict[str, list[str]]) -> None:
    for message in state.chat_buffer:
        if not message.id:
            message.like_count = 0
            message.liked_by_user_ids = []
            continue
        user_ids = likes_by_message_id.get(message.id, [])
        message.liked_by_user_ids = user_ids
        message.like_count = len(user_ids)


async def scene_to_response_with_likes(
    db: AsyncSession,
    scene: Scene,
    *,
    viewer_role: str = "MASTER",
) -> SceneResponse:
    response = scene_to_response(scene, viewer_role=viewer_role)
    message_ids = [message.id for message in response.scene_state.chat_buffer if message.id]
    likes = await fetch_likes_by_message_id(db, scene.id, message_ids)
    apply_likes_to_scene_state(response.scene_state, likes)
    return response


async def toggle_scene_message_like(
    db: AsyncSession,
    scene: Scene,
    user_id: str,
    message_id: str,
) -> SceneResponse:
    trimmed_id = message_id.strip()
    if not trimmed_id:
        raise SceneServiceError("Message id is required")

    state = load_scene_state(scene)
    in_buffer = any(entry.id == trimmed_id for entry in state.chat_buffer)
    if not in_buffer:
        persisted = await db.get(SceneMessage, trimmed_id)
        if persisted is None or persisted.scene_id != scene.id:
            raise SceneServiceError("Message not found")

    await toggle_message_like(db, scene.id, trimmed_id, uuid.UUID(user_id))
    await db.commit()
    await db.refresh(scene)
    return await scene_to_response_with_likes(db, scene)


async def _next_assigned_scene_number(db: AsyncSession, campaign_id: uuid.UUID) -> int:
    current_max = await db.scalar(
        select(func.coalesce(func.max(Scene.scene_number), 0)).where(
            Scene.campaign_id == campaign_id,
            Scene.status.in_(("ACTIVE", "PAUSED", "CLOSED")),
            Scene.scene_number.is_not(None),
        )
    )
    return int(current_max or 0) + 1


def _parse_entity_uuid_set(values: set[str]) -> list[uuid.UUID]:
    parsed: list[uuid.UUID] = []
    for value in values:
        try:
            parsed.append(uuid.UUID(str(value).strip()))
        except ValueError:
            continue
    return parsed


def _normalize_display_name(display_name: str | None) -> str | None:
    if display_name is None:
        return None
    trimmed = display_name.strip()
    return trimmed or None


def _build_narrative_text(
    state: SceneState,
    *,
    last_n: int | None = None,
    messages: list[ChatMessage] | None = None,
) -> str:
    lines: list[str] = []
    source = messages if messages is not None else state.chat_buffer
    for message in source:
        if message.type not in NARRATIVE_MESSAGE_TYPES:
            continue
        text = (message.text or "").strip()
        if text:
            lines.append(text)
    if last_n is not None and last_n > 0:
        lines = lines[-last_n:]
    return "\n".join(lines)


async def append_chat_message(
    db: AsyncSession,
    scene: Scene,
    state: SceneState,
    message: ChatMessage | dict,
) -> ChatMessage:
    msg = ChatMessage.model_validate(message)
    await persist_scene_message(db, scene.id, msg)
    state.chat_buffer.append(msg)
    state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]
    return msg


def _placeholder_scene_summary(
    narrative: str,
    *,
    scene_number: int,
    display_name: str | None,
) -> str:
    title = f"Escena {scene_number}"
    if display_name:
        title = f"{title}: {display_name}"
    if not narrative.strip():
        return f"{title} — cerrada sin mensajes narrativos registrados."
    truncated = narrative[:500].rstrip()
    if len(narrative) > 500:
        truncated = f"{truncated}..."
    return f"{title}\n\n{truncated}"


async def generate_scene_closure_summary(
    state: SceneState,
    *,
    scene_number: int,
    display_name: str | None,
    db: AsyncSession | None = None,
    scene_id: uuid.UUID | None = None,
) -> str:
    messages = state.chat_buffer
    if db is not None and scene_id is not None:
        messages = await list_all_scene_messages(db, scene_id)
        if not messages:
            messages = state.chat_buffer

    narrative = _build_narrative_text(state, messages=messages)
    if not narrative.strip():
        return _placeholder_scene_summary(
            narrative,
            scene_number=scene_number,
            display_name=display_name,
        )

    scene_label = f"Escena {scene_number}"
    if display_name:
        scene_label = f"{scene_label} ({display_name})"

    try:
        summary = await chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "Eres un cronista de rol. Resume la escena en español en 2-4 frases claras, "
                        "sin inventar eventos que no aparezcan en el chat."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Resume lo ocurrido en {scene_label}:\n\n{narrative[:8000]}",
                },
            ],
            temperature=0.3,
            max_tokens=400,
        )
        if summary.strip():
            return summary.strip()
    except LLMNotConfiguredError:
        pass
    except LLMError:
        pass

    return _placeholder_scene_summary(
        _build_narrative_text(state, last_n=FALLBACK_SUMMARY_MESSAGE_COUNT, messages=messages),
        scene_number=scene_number,
        display_name=display_name,
    )


async def delete_scene_message(
    db: AsyncSession,
    scene: Scene,
    message_id: str,
) -> SceneResponse:
    if scene.status == "CLOSED":
        raise SceneServiceError("Cannot delete messages from a closed scene")

    trimmed_id = message_id.strip()
    if not trimmed_id:
        raise SceneServiceError("Message id is required")

    state = load_scene_state(scene)
    original_len = len(state.chat_buffer)
    state.chat_buffer = [entry for entry in state.chat_buffer if entry.id != trimmed_id]
    removed_from_buffer = len(state.chat_buffer) != original_len
    removed_from_store = await delete_persisted_scene_message(db, scene.id, trimmed_id)
    if not removed_from_buffer and not removed_from_store:
        raise SceneServiceError("Message not found")

    save_scene_state(scene, state)
    await delete_likes_for_message(db, scene.id, trimmed_id)
    await db.commit()
    await db.refresh(scene)
    return await scene_to_response_with_likes(db, scene)


async def list_campaign_scenes(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    viewer_role: str = "MASTER",
) -> list[SceneResponse]:
    scenes = (
        await db.scalars(
            select(Scene)
            .where(Scene.campaign_id == campaign_id)
            .order_by(Scene.scene_number.asc().nulls_last(), Scene.created_at.asc())
        )
    ).all()
    if viewer_role != "MASTER":
        scenes = [scene for scene in scenes if scene.status != "PREPARED"]
    return [scene_to_response(scene, viewer_role=viewer_role) for scene in scenes]


async def list_prepared_scenes(db: AsyncSession, campaign_id: uuid.UUID) -> list[ScenePickerItem]:
    scenes = (
        await db.scalars(
            select(Scene)
            .where(Scene.campaign_id == campaign_id, Scene.status == "PREPARED")
            .order_by(Scene.created_at.asc())
        )
    ).all()
    items: list[ScenePickerItem] = []
    for scene in scenes:
        state = load_scene_state(scene)
        items.append(
            ScenePickerItem(
                id=str(scene.id),
                scene_number=scene.scene_number,
                display_name=scene.display_name,
                scene_objective=state.context.scene_objective,
                status=scene.status,
            )
        )
    return items


async def get_active_scene(db: AsyncSession, campaign_id: uuid.UUID) -> Scene | None:
    return await db.scalar(
        select(Scene)
        .where(Scene.campaign_id == campaign_id, Scene.status == "ACTIVE")
        .order_by(Scene.updated_at.desc(), Scene.created_at.desc())
        .limit(1)
    )


async def get_open_scene(db: AsyncSession, campaign_id: uuid.UUID) -> Scene | None:
    """Latest ACTIVE or PAUSED scene for unread counts and player chat access."""
    return await db.scalar(
        select(Scene)
        .where(
            Scene.campaign_id == campaign_id,
            Scene.status.in_(("ACTIVE", "PAUSED")),
        )
        .order_by(Scene.scene_number.desc(), Scene.updated_at.desc())
        .limit(1)
    )


async def require_no_other_open_scene(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    except_scene_id: uuid.UUID | None = None,
) -> None:
    open_scene = await get_open_scene(db, campaign_id)
    if open_scene is None:
        return
    if except_scene_id is not None and open_scene.id == except_scene_id:
        return
    raise SceneServiceError(OPEN_SCENE_BLOCK_MESSAGE)


async def close_other_open_scenes(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    except_scene_id: uuid.UUID | None = None,
) -> list[Scene]:
    """Close every other ACTIVE/PAUSED scene so at most one remains open."""
    query = select(Scene).where(
        Scene.campaign_id == campaign_id,
        Scene.status.in_(("ACTIVE", "PAUSED")),
    )
    if except_scene_id is not None:
        query = query.where(Scene.id != except_scene_id)

    scenes = (await db.scalars(query)).all()
    for other in scenes:
        state = load_scene_state(other)
        if not (state.metadata.closure_summary or "").strip():
            state.metadata.closure_summary = AUTO_CLOSED_SCENE_NOTE
        state.metadata.status = "CLOSED"
        state.context.master_scene_scratchpad = None
        if state.combat.is_active or state.combat.conflict_mode_active or state.state_flags.conflict_mode_active:
            set_combat_active(state, False)
        save_scene_state(other, state)
    return list(scenes)


async def pause_other_active_scenes(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    except_scene_id: uuid.UUID | None = None,
) -> list[Scene]:
    """Deprecated alias: closes other open scenes (kept for tests/scripts)."""
    return await close_other_open_scenes(db, campaign_id, except_scene_id=except_scene_id)


async def get_scene_by_id(db: AsyncSession, scene_id: uuid.UUID) -> Scene | None:
    return await db.scalar(select(Scene).where(Scene.id == scene_id))


async def create_scene(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    payload: SceneCreate,
    creator_user_id: uuid.UUID,
) -> SceneResponse:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        raise SceneServiceError("Campaign not found")

    target_status = payload.status
    if target_status in ("ACTIVE", "PAUSED"):
        await close_other_open_scenes(db, campaign_id)

    turn_order = payload.turn_order or [str(creator_user_id)]
    scene_state = default_scene_state(
        str(campaign_id),
        turn_order=turn_order,
        scene_objective=payload.scene_objective,
        location_id=payload.location_id,
        opening_narration=payload.opening_narration,
        master_prep_notes=payload.master_prep_notes,
        prepared_entity_refs=payload.prepared_entity_refs,
        status=target_status,
    )
    display_name = _normalize_display_name(payload.display_name)
    scene_number: int | None
    if target_status == "PREPARED":
        scene_number = None
    else:
        scene_number = await _next_assigned_scene_number(db, campaign_id)

    scene = Scene(
        campaign_id=campaign_id,
        scene_number=scene_number,
        display_name=display_name,
        status=target_status,
        scene_state=scene_state.model_dump(),
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

    if target_status == "ACTIVE":
        await mark_all_campaign_pcs_present_for_scene(db, scene)
        await db.refresh(scene)

    return scene_to_response(scene)


async def post_message(
    db: AsyncSession,
    scene: Scene,
    sender_id: str,
    payload: PostMessageRequest,
    *,
    sender_role: str = "PLAYER",
) -> SceneResponse:
    ensure_scene_post_allowed(scene, sender_role=sender_role)

    msg_type = normalize_message_type(payload.type)
    if msg_type == "MASTER" and sender_role != "MASTER":
        raise SceneServiceError("Master messages require MASTER role")

    state = load_scene_state(scene)

    try:
        await assert_pbp_post_allowed(
            db, scene.campaign_id, state, sender_id, sender_role
        )
    except PbpTurnError as exc:
        raise SceneServiceError(str(exc)) from exc

    speaker_fields = await resolve_message_speaker_fields(
        db,
        scene,
        payload,
        sender_id=sender_id,
        sender_role=sender_role,
        msg_type=msg_type,
    )

    text = (payload.text or "").strip()
    image_url = (payload.image_url or "").strip() or None

    if image_url and sender_role != "MASTER":
        raise SceneServiceError("Solo el Máster puede adjuntar imágenes al chat")

    if image_url:
        try:
            validate_message_image_url(scene, image_url)
        except ChatMessageImageError as exc:
            raise SceneServiceError(str(exc)) from exc

    message = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "sender_id": sender_id,
        "type": msg_type,
        "text": text or None,
        "image_url": image_url,
        "read_by": [sender_id],
        **speaker_fields,
    }
    await append_chat_message(db, scene, state, message)

    if sender_role != "MASTER" and msg_type in NARRATIVE_MESSAGE_TYPES:
        advance_pbp_turn(state)
        if state.combat.initiative_order:
            await sync_turn_management_from_initiative(db, scene.campaign_id, state)

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)

    if text:
        await rag_service.index_message(
            db,
            campaign_id=state.metadata.campaign_id,
            document_id=message["id"],
            text=text,
            metadata={"scene_id": str(scene.id), "sender_id": sender_id, "type": msg_type},
        )
    return scene_to_response(scene)


async def roll_scene_dice(
    db: AsyncSession,
    scene: Scene,
    sender_id: str,
    payload: DiceRollRequest,
    *,
    sender_role: str = "PLAYER",
) -> SceneResponse:
    ensure_scene_post_allowed(scene, sender_role=sender_role)

    if payload.master_only and sender_role != "MASTER":
        raise SceneServiceError("Solo el Máster puede tirar en secreto")

    state = load_scene_state(scene)

    try:
        await assert_pbp_post_allowed(
            db, scene.campaign_id, state, sender_id, sender_role
        )
    except PbpTurnError as exc:
        raise SceneServiceError(str(exc)) from exc

    campaign = await get_campaign_or_error(db, scene.campaign_id)

    from app.services.entities import resolve_roll_visibility

    try:
        result = roll_dice_expression(
            payload.dice_expression,
            payload.modifier,
            game_system=campaign.game_system,
            advantage=payload.advantage,
            disadvantage=payload.disadvantage,
        )
    except ValueError as exc:
        raise SceneServiceError(str(exc)) from exc

    summary = result.get("chat_summary") or format_raw_roll_summary(payload.dice_expression, result)
    roll_details = result.get("roll_details") or build_generic_roll_details(payload.dice_expression, result)

    visibility = await resolve_roll_visibility(
        db,
        scene.campaign_id,
        master_only=payload.master_only,
        sender_role=sender_role,
    )

    speaker_fields = await resolve_dice_roll_speaker_fields(
        db,
        scene.campaign_id,
        sender_id=sender_id,
        sender_role=sender_role,
    )

    message = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "sender_id": sender_id,
        "type": "DICE_ROLL",
        "text": summary,
        "chat_summary": summary,
        "dice_expression": payload.dice_expression,
        "rolls": result.get("rolls"),
        "raw_result": result["raw_result"],
        "final_result": result["final_result"],
        "skill_checked": payload.skill_checked,
        "roll_details": roll_details,
        "read_by": [sender_id],
        "visibility": visibility,
        **speaker_fields,
    }
    await append_chat_message(db, scene, state, message)

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def mark_messages_read(
    db: AsyncSession,
    scene: Scene,
    user_id: str,
    message_ids: list[str] | None = None,
) -> SceneResponse:
    state = load_scene_state(scene)
    buffer = [entry.model_dump() for entry in state.chat_buffer]

    for entry in buffer:
        if message_ids is not None and entry["id"] not in message_ids:
            continue
        if user_id not in entry["read_by"]:
            entry["read_by"].append(user_id)

    state.chat_buffer = [ChatMessage.model_validate(entry) for entry in buffer]
    await update_persisted_read_by(db, scene.id, user_id, message_ids)
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def update_scene_status(
    db: AsyncSession,
    scene: Scene,
    status: SceneStatusType,
) -> SceneResponse:
    if status in ("ACTIVE", "PAUSED"):
        await close_other_open_scenes(db, scene.campaign_id, except_scene_id=scene.id)

    state = load_scene_state(scene)
    state.metadata.status = status
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)

    if status == "ACTIVE":
        await mark_all_campaign_pcs_present_for_scene(db, scene)
        await db.refresh(scene)

    return scene_to_response(scene)


async def update_scene_display_name(
    db: AsyncSession,
    scene: Scene,
    display_name: str | None,
) -> SceneResponse:
    scene.display_name = _normalize_display_name(display_name)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def update_scene_prep(
    db: AsyncSession,
    scene: Scene,
    payload: ScenePrepUpdate,
) -> SceneResponse:
    if scene.status == "CLOSED":
        raise SceneServiceError("Cannot edit a closed scene")

    state = load_scene_state(scene)
    if payload.display_name is not None:
        scene.display_name = _normalize_display_name(payload.display_name)
    if payload.scene_objective is not None:
        state.context.scene_objective = payload.scene_objective.strip() or None
    if payload.location_id is not None:
        state.context.location_id = payload.location_id.strip() or None
    if payload.opening_narration is not None:
        state.context.opening_narration = payload.opening_narration.strip() or None
    if payload.master_prep_notes is not None:
        state.context.master_prep_notes = payload.master_prep_notes.strip() or None
    if payload.prepared_entity_refs is not None:
        state.context.prepared_entity_refs = await _normalize_prepared_entity_refs(
            db,
            scene.campaign_id,
            list(payload.prepared_entity_refs),
        )

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def update_scene_scratchpad(
    db: AsyncSession,
    scene: Scene,
    payload: SceneScratchpadUpdate,
) -> SceneResponse:
    if scene.status == "CLOSED":
        raise SceneServiceError("Cannot edit a closed scene")

    state = load_scene_state(scene)
    if payload.master_scene_scratchpad is not None:
        state.context.master_scene_scratchpad = payload.master_scene_scratchpad.strip() or None

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def _normalize_prepared_entity_refs(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    refs: list[PreparedEntityRef],
) -> list[PreparedEntityRef]:
    if not refs:
        return []

    entity_ids: list[uuid.UUID] = []
    for ref in refs:
        try:
            entity_ids.append(uuid.UUID(str(ref.entity_id).strip()))
        except ValueError:
            continue

    if not entity_ids:
        return list(refs)

    entities = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == campaign_id,
                CampaignEntity.id.in_(entity_ids),
            )
        )
    ).all()
    pc_ids = {str(entity.id) for entity in entities if entity.entity_type == "PC"}

    return [
        ref.model_copy(update={"player_visibility": "visible"})
        if str(ref.entity_id).strip() in pc_ids
        else ref
        for ref in refs
    ]


async def _apply_prepared_entity_refs(
    db: AsyncSession,
    scene: Scene,
    state: SceneState,
    refs: list[PreparedEntityRef],
) -> None:
    from app.services.entities import set_pc_present_in_scene

    if not refs:
        return

    entity_ids = [str(ref.entity_id).strip() for ref in refs if str(ref.entity_id).strip()]
    entities = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == scene.campaign_id,
                CampaignEntity.id.in_([uuid.UUID(value) for value in entity_ids]),
            )
        )
    ).all()
    entities_by_id = {str(entity.id): entity for entity in entities}
    missing = set(entity_ids) - set(entities_by_id)
    if missing:
        raise SceneServiceError(f"Entity not found in campaign: {', '.join(sorted(missing))}")

    npc_add: list[NpcPresenceEntry] = []
    for ref in refs:
        entity_id = str(ref.entity_id).strip()
        entity = entities_by_id.get(entity_id)
        if entity is None:
            continue

        if entity.entity_type == "NPC":
            flags = dict(entity.document.get("state_flags") or {})
            visibility = ref.player_visibility
            if visibility in ("hidden", "unknown", "visible"):
                flags["player_visibility"] = visibility
                flags["hidden_from_players"] = visibility == "hidden"
                entity.document = {**entity.document, "state_flags": flags}

            if ref.add_to_roster:
                npc_add.append(
                    NpcPresenceEntry(
                        entity_id=entity_id,
                        is_hidden_from_players=visibility in ("hidden", "unknown"),
                    )
                )
        elif entity.entity_type == "PC":
            # PCs are always visible to players; ignore player_visibility on ref.
            if ref.add_to_roster:
                await set_pc_present_in_scene(db, entity, present=True, commit=False)

    if npc_add:
        _apply_npc_presence_to_state(state, add=npc_add, remove=[])


async def activate_scene(
    db: AsyncSession,
    scene: Scene,
    *,
    send_opening_to_chat: bool = False,
    activator_user_id: str | None = None,
) -> SceneResponse:
    if scene.status == "CLOSED":
        raise SceneServiceError("Cannot activate a closed scene")
    if scene.status == "ACTIVE":
        return scene_to_response(scene)

    await close_other_open_scenes(db, scene.campaign_id, except_scene_id=scene.id)

    if scene.scene_number is None:
        scene.scene_number = await _next_assigned_scene_number(db, scene.campaign_id)

    state = load_scene_state(scene)
    refs = await _normalize_prepared_entity_refs(
        db,
        scene.campaign_id,
        list(state.context.prepared_entity_refs),
    )
    await _apply_prepared_entity_refs(db, scene, state, refs)

    state.metadata.status = "ACTIVE"
    save_scene_state(scene, state)
    scene.status = "ACTIVE"

    opening = (state.context.opening_narration or "").strip()
    if send_opening_to_chat and opening and activator_user_id:
        message = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now_iso(),
            "sender_id": activator_user_id,
            "type": "ACTION",
            "text": opening,
            "read_by": [activator_user_id],
            "speaker_type": "NARRATOR",
            "speaker_display_name": DEFAULT_NARRATOR_DISPLAY_NAME,
            "speaker_entity_id": None,
        }
        await append_chat_message(db, scene, state, message)
        save_scene_state(scene, state)

    await db.commit()
    await db.refresh(scene)

    await mark_all_campaign_pcs_present_for_scene(db, scene)
    await db.refresh(scene)
    return scene_to_response(scene)


async def start_active_scene(
    db: AsyncSession,
    scene: Scene,
    *,
    send_opening_to_chat: bool = False,
    activator_user_id: str | None = None,
) -> SceneResponse:
    return await activate_scene(
        db,
        scene,
        send_opening_to_chat=send_opening_to_chat,
        activator_user_id=activator_user_id,
    )


async def delete_scene(db: AsyncSession, scene: Scene) -> None:
    scene_id = str(scene.id)
    campaign_id = str(scene.campaign_id)

    await db.execute(delete(SceneMessageLike).where(SceneMessageLike.scene_id == scene.id))
    await db.execute(delete(SceneMessage).where(SceneMessage.scene_id == scene.id))
    await db.execute(
        delete(CampaignMemory).where(
            CampaignMemory.campaign_id == scene.campaign_id,
            or_(
                CampaignMemory.metadata_["scene_id"].as_string() == scene_id,
                CampaignMemory.metadata_["document_id"].astext == scene_id,
                CampaignMemory.id == scene.id,
            ),
        )
    )
    await db.delete(scene)
    await db.commit()
    await rag_service.purge_semantic_cache(db, campaign_id=campaign_id)


async def close_scene(db: AsyncSession, scene: Scene) -> CloseSceneResponse:
    if scene.status == "CLOSED":
        raise SceneServiceError("Scene is already closed")

    state = load_scene_state(scene)
    scene_number = scene.scene_number
    if scene_number is None:
        scene_number = await _next_assigned_scene_number(db, scene.campaign_id)
        scene.scene_number = scene_number

    summary = await generate_scene_closure_summary(
        state,
        scene_number=scene_number,
        display_name=scene.display_name,
        db=db,
        scene_id=scene.id,
    )
    state.metadata.closure_summary = summary
    state.metadata.status = "CLOSED"
    state.context.master_scene_scratchpad = None
    if state.combat.is_active or state.combat.conflict_mode_active or state.state_flags.conflict_mode_active:
        set_combat_active(state, False)
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)

    await rag_service.index_message(
        db,
        campaign_id=str(scene.campaign_id),
        document_id=str(scene.id),
        text=summary,
        metadata={
            "scene_id": str(scene.id),
            "scene_number": scene.scene_number,
            "display_name": scene.display_name,
        },
        document_type=MemoryDocumentType.SCENE_SUMMARY,
    )
    await rag_service.purge_semantic_cache(db, campaign_id=str(scene.campaign_id))

    prepared_scenes = await list_prepared_scenes(db, scene.campaign_id)
    return CloseSceneResponse(
        closed_scene=scene_to_response(scene),
        prepared_scenes=prepared_scenes,
    )


async def get_master_briefing(db: AsyncSession, scene: Scene) -> MasterBriefingResponse:
    state = load_scene_state(scene)
    next_scene_number = await _next_assigned_scene_number(db, scene.campaign_id)
    open_scene_row = await get_open_scene(db, scene.campaign_id)
    open_scene = None
    if open_scene_row is not None and open_scene_row.id != scene.id:
        open_scene = MasterBriefingOpenScene(
            id=str(open_scene_row.id),
            scene_number=open_scene_row.scene_number,
            display_name=open_scene_row.display_name,
            status=open_scene_row.status,
        )

    last_summary: str | None = None
    last_closed = await db.scalar(
        select(Scene)
        .where(Scene.campaign_id == scene.campaign_id, Scene.status == "CLOSED")
        .order_by(Scene.scene_number.desc(), Scene.updated_at.desc())
        .limit(1)
    )
    if last_closed is not None:
        closed_state = load_scene_state(last_closed)
        last_summary = closed_state.metadata.closure_summary

    arc_manifest: dict | None = None
    arc_entity = await db.scalar(
        select(CampaignEntity).where(
            CampaignEntity.campaign_id == scene.campaign_id,
            CampaignEntity.entity_type == "ARC_MANIFEST",
        )
    )
    if arc_entity is not None:
        arc_manifest = dict(arc_entity.document)

    location: MasterBriefingLocation | None = None
    location_id = state.context.location_id
    if location_id:
        location_entity = await db.scalar(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == scene.campaign_id,
                CampaignEntity.id == uuid.UUID(str(location_id)),
            )
        )
        if location_entity is not None:
            identity = location_entity.document.get("identity", {})
            name = identity.get("name", str(location_id)[:8]) if isinstance(identity, dict) else str(location_id)[:8]
            location = MasterBriefingLocation(id=str(location_entity.id), name=str(name))

    from app.services.entities import npc_player_visibility

    refs = list(state.context.prepared_entity_refs)
    ref_entity_ids = {str(ref.entity_id) for ref in refs}
    npc_ids = set(state.context.active_npc_ids) | ref_entity_ids
    npc_uuid_ids = _parse_entity_uuid_set(npc_ids)

    npc_entries: list[MasterBriefingNpcEntry] = []
    if npc_uuid_ids:
        npcs = (
            await db.scalars(
                select(CampaignEntity).where(
                    CampaignEntity.campaign_id == scene.campaign_id,
                    CampaignEntity.entity_type == "NPC",
                    CampaignEntity.id.in_(npc_uuid_ids),
                )
            )
        ).all()
        refs_by_id = {str(ref.entity_id): ref for ref in refs}
        for npc in npcs:
            entity_id = str(npc.id)
            identity = npc.document.get("identity", {})
            name = identity.get("name", entity_id[:8]) if isinstance(identity, dict) else entity_id[:8]
            profile = npc.document.get("ai_narrative_profile", {})
            voice = profile.get("voice_and_tone") if isinstance(profile, dict) else None
            secret = profile.get("secret_lore_master") if isinstance(profile, dict) else None
            ref = refs_by_id.get(entity_id)
            visibility = ref.player_visibility if ref else npc_player_visibility(npc.document)
            npc_entries.append(
                MasterBriefingNpcEntry(
                    entity_id=entity_id,
                    name=str(name),
                    voice_and_tone=str(voice) if voice else None,
                    secret_lore_master=str(secret) if secret else None,
                    player_visibility=visibility,
                    in_roster=ref.add_to_roster if ref else entity_id in state.context.active_npc_ids,
                )
            )

    return MasterBriefingResponse(
        scene_id=str(scene.id),
        display_name=scene.display_name,
        next_scene_number=next_scene_number,
        open_scene=open_scene,
        scene_objective=state.context.scene_objective,
        location=location,
        opening_narration=state.context.opening_narration,
        master_prep_notes=state.context.master_prep_notes,
        last_scene_summary=last_summary,
        arc_manifest=arc_manifest,
        npcs=npc_entries,
        prepared_entity_refs=refs,
    )


def _normalize_npc_id_list(ids: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_id in ids:
        value = str(raw_id).strip()
        if not value or value in seen:
            continue
        normalized.append(value)
        seen.add(value)
    return normalized


def _apply_npc_presence_to_state(
    state: SceneState,
    *,
    add: list[NpcPresenceEntry],
    remove: list[str],
) -> None:
    active_ids = _normalize_npc_id_list(state.context.active_npc_ids)
    hidden_ids = set(_normalize_npc_id_list(state.context.hidden_npc_ids))

    for raw_id in remove:
        entity_id = str(raw_id).strip()
        if entity_id in active_ids:
            active_ids.remove(entity_id)
        hidden_ids.discard(entity_id)

    for entry in add:
        entity_id = str(entry.entity_id).strip()
        if not entity_id:
            continue
        if entity_id not in active_ids:
            active_ids.append(entity_id)
        if entry.is_hidden_from_players:
            hidden_ids.add(entity_id)
        else:
            hidden_ids.discard(entity_id)

    state.context.active_npc_ids = active_ids
    state.context.hidden_npc_ids = _normalize_npc_id_list(
        [entity_id for entity_id in hidden_ids if entity_id in active_ids]
    )


async def update_scene_npc_presence(
    db: AsyncSession,
    scene: Scene,
    payload: ScenePresenceUpdate,
) -> SceneResponse:
    state = load_scene_state(scene)
    _apply_npc_presence_to_state(state, add=payload.add, remove=payload.remove)

    npc_ids_to_validate = {
        str(entry.entity_id).strip()
        for entry in payload.add
        if str(entry.entity_id).strip()
    }
    if npc_ids_to_validate:
        npcs = (
            await db.scalars(
                select(CampaignEntity).where(
                    CampaignEntity.campaign_id == scene.campaign_id,
                    CampaignEntity.entity_type == "NPC",
                    CampaignEntity.id.in_([uuid.UUID(value) for value in npc_ids_to_validate]),
                )
            )
        ).all()
        found_ids = {str(npc.id) for npc in npcs}
        missing = npc_ids_to_validate - found_ids
        if missing:
            raise SceneServiceError(f"NPC not found in campaign: {', '.join(sorted(missing))}")

        from app.services.entities import npc_player_visibility

        for entry in payload.add:
            entity_id = str(entry.entity_id).strip()
            npc = next((item for item in npcs if str(item.id) == entity_id), None)
            if npc is None:
                continue
            current = npc_player_visibility(npc.document)
            if current == "hidden":
                continue
            next_visibility = "unknown" if entry.is_hidden_from_players else "visible"
            if current == next_visibility:
                continue
            flags = dict(npc.document.get("state_flags") or {})
            flags["player_visibility"] = next_visibility
            flags["hidden_from_players"] = False
            npc.document = {**npc.document, "state_flags": flags}

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def resolve_dice_roll_speaker_fields(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    sender_id: str,
    sender_role: str,
    entity_id: str | None = None,
) -> dict[str, str]:
    if entity_id:
        entities = await fetch_entities_by_id(db, campaign_id, [entity_id])
        entity = entities.get(entity_id)
        if entity is not None:
            name = entity_display_name(entity)
            speaker_type = "NPC" if entity.entity_type == "NPC" else "PC"
            return {
                "entity_id": entity_id,
                "entity_name": name,
                "speaker_display_name": name,
                "speaker_type": speaker_type,
            }

    if sender_role == "MASTER":
        return {
            "speaker_display_name": MASTER_DICE_ROLL_DISPLAY_NAME,
            "speaker_type": "MASTER",
        }

    try:
        user_uuid = uuid.UUID(str(sender_id))
    except ValueError:
        return {}

    pc = await find_pc_by_user(db, campaign_id, user_uuid)
    if pc is None:
        return {}

    name = entity_display_name(pc)
    return {
        "entity_id": str(pc.id),
        "entity_name": name,
        "speaker_display_name": name,
        "speaker_type": "PC",
    }


def build_dice_roll_message(
    *,
    sender_id: str,
    roll_result: dict[str, Any],
    entity_id: str | None = None,
    entity_name: str | None = None,
    speaker_display_name: str | None = None,
    speaker_type: str | None = None,
    skill_checked: str | None = None,
    visibility: str = "all",
) -> dict[str, Any]:
    roll_details = roll_result.get("roll_details")
    if not isinstance(roll_details, dict):
        roll_details = {}

    roll_label = roll_details.get("roll_label")
    if isinstance(roll_label, str) and roll_label.strip():
        skill_checked = skill_checked or roll_label.strip()

    text = roll_result.get("chat_summary")
    if not isinstance(text, str) or not text.strip():
        expression = roll_result.get("dice_expression", "")
        final_result = roll_result.get("final_result")
        text = f"Roll: {expression} => {final_result}"

    message: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "sender_id": sender_id,
        "type": "DICE_ROLL",
        "text": text,
        "dice_expression": roll_result.get("dice_expression"),
        "rolls": roll_result.get("rolls"),
        "raw_result": roll_result.get("raw_result"),
        "final_result": roll_result.get("final_result"),
        "skill_checked": skill_checked,
        "chat_summary": roll_result.get("chat_summary"),
        "success": roll_result.get("success"),
        "read_by": [sender_id],
        "visibility": visibility,
    }
    if entity_id:
        message["entity_id"] = entity_id
    if entity_name:
        message["entity_name"] = entity_name
    if speaker_display_name:
        message["speaker_display_name"] = speaker_display_name
    if speaker_type:
        message["speaker_type"] = speaker_type
    if roll_result.get("roll_type"):
        message["roll_type"] = roll_result["roll_type"]
    if roll_details:
        message["roll_details"] = roll_details
    return message


async def append_dice_roll_to_scene(
    db: AsyncSession,
    scene: Scene,
    *,
    sender_id: str,
    roll_result: dict[str, Any],
    entity_id: str | None = None,
    skill_checked: str | None = None,
    visibility: str = "all",
    sender_role: str = "PLAYER",
) -> SceneResponse:
    ensure_scene_post_allowed(scene, sender_role=sender_role)
    state = load_scene_state(scene)
    speaker_fields = await resolve_dice_roll_speaker_fields(
        db,
        scene.campaign_id,
        sender_id=sender_id,
        sender_role=sender_role,
        entity_id=entity_id,
    )
    message = build_dice_roll_message(
        sender_id=sender_id,
        roll_result=roll_result,
        entity_id=speaker_fields.get("entity_id", entity_id),
        entity_name=speaker_fields.get("entity_name"),
        speaker_display_name=speaker_fields.get("speaker_display_name"),
        speaker_type=speaker_fields.get("speaker_type"),
        skill_checked=skill_checked,
        visibility=visibility,
    )
    await append_chat_message(db, scene, state, message)
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def update_scene_turn_management(
    db: AsyncSession,
    scene: Scene,
    payload: SceneTurnManagementUpdate,
) -> SceneResponse:
    state = load_scene_state(scene)

    if payload.pbp_enabled is not None:
        state.turn_management.pbp_enabled = payload.pbp_enabled
        if payload.pbp_enabled:
            await ensure_pbp_initiative_order(db, scene.campaign_id, state)
    if payload.order_source is not None:
        state.turn_management.order_source = payload.order_source

    if payload.turn_order is not None:
        state.turn_management.turn_order = [str(user_id) for user_id in payload.turn_order]
        if payload.current_turn_player_id is None:
            if state.turn_management.turn_order:
                current = state.turn_management.current_turn_player_id
                if current not in state.turn_management.turn_order:
                    state.turn_management.current_turn_player_id = state.turn_management.turn_order[0]
            else:
                state.turn_management.current_turn_player_id = None

    if payload.current_turn_player_id is not None:
        state.turn_management.current_turn_player_id = payload.current_turn_player_id

    if (
        payload.current_turn_entity_id is not None
        and payload.initiative_order is None
    ):
        if not state.combat.initiative_order:
            await ensure_pbp_initiative_order(db, scene.campaign_id, state)
        entity_id = str(payload.current_turn_entity_id)
        known_ids = {str(entry.entity_id) for entry in state.combat.initiative_order}
        if entity_id not in known_ids:
            raise SceneServiceError("Entity is not in the current turn order")
        state.combat.current_turn_entity_id = entity_id
        await sync_turn_management_from_initiative(db, scene.campaign_id, state)

    if payload.initiative_order is not None:
        entries = list(payload.initiative_order)
        entity_ids = [str(entry.entity_id) for entry in entries]
        entities_by_id = await fetch_entities_by_id(db, scene.campaign_id, entity_ids)
        order_source = state.turn_management.order_source
        if payload.resort:
            entries = sort_initiative_entries(entries, entities_by_id, order_source)
        state.combat.initiative_order = entries
        if payload.current_turn_entity_id is not None:
            state.combat.current_turn_entity_id = payload.current_turn_entity_id
        elif entries:
            state.combat.current_turn_entity_id = entries[0].entity_id
        await sync_turn_management_from_initiative(db, scene.campaign_id, state)
    elif payload.resort and state.combat.initiative_order:
        entity_ids = [str(entry.entity_id) for entry in state.combat.initiative_order]
        entities_by_id = await fetch_entities_by_id(db, scene.campaign_id, entity_ids)
        state.combat.initiative_order = sort_initiative_entries(
            state.combat.initiative_order,
            entities_by_id,
            state.turn_management.order_source,
        )
        if state.combat.initiative_order:
            state.combat.current_turn_entity_id = state.combat.initiative_order[0].entity_id
        await sync_turn_management_from_initiative(db, scene.campaign_id, state)

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def advance_scene_pbp_turn(
    db: AsyncSession,
    scene: Scene,
) -> SceneResponse:
    state = load_scene_state(scene)
    if not is_pbp_enforcement_active(state):
        raise SceneServiceError("PBP mode is not enabled")

    if not state.combat.initiative_order:
        populated = await ensure_pbp_initiative_order(db, scene.campaign_id, state)
        if not populated:
            raise SceneServiceError("No turn order defined")

    advance_pbp_turn(state)
    await sync_turn_management_from_initiative(db, scene.campaign_id, state)
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def _append_pc_to_pbp_initiative_if_needed(
    db: AsyncSession,
    scene: Scene,
    pc: CampaignEntity,
    state: SceneState,
) -> None:
    """Keep PBP turn track in sync when a PC joins the active scene."""
    if not is_pbp_enforcement_active(state):
        return

    entity_id = str(pc.id)
    known_ids = {str(entry.entity_id) for entry in state.combat.initiative_order}
    if entity_id in known_ids:
        return

    binding = pc.document.get("player_binding", {})
    user_id = (
        str(binding["user_id"])
        if isinstance(binding, dict) and binding.get("user_id")
        else None
    )

    if state.combat.initiative_order:
        state.combat.initiative_order.append(
            InitiativeEntry(
                entity_id=entity_id,
                entity_type="PC",
                display_name=entity_display_name(pc),
                is_active=True,
            )
        )
        await sync_turn_management_from_initiative(db, scene.campaign_id, state)
        return

    if state.turn_management.turn_order and user_id:
        if user_id not in state.turn_management.turn_order:
            state.turn_management.turn_order.append(user_id)
        return

    populated = await ensure_pbp_initiative_order(db, scene.campaign_id, state)
    if populated or entity_id in {str(entry.entity_id) for entry in state.combat.initiative_order}:
        return

    state.combat.initiative_order.append(
        InitiativeEntry(
            entity_id=entity_id,
            entity_type="PC",
            display_name=entity_display_name(pc),
            is_active=True,
        )
    )
    await sync_turn_management_from_initiative(db, scene.campaign_id, state)


async def _apply_pc_presence_to_scene(
    db: AsyncSession,
    scene: Scene,
    pc: CampaignEntity,
    *,
    state: SceneState | None = None,
) -> SceneState:
    from app.services.entities import set_pc_present_in_scene

    if pc.entity_type != "PC" or pc.campaign_id != scene.campaign_id:
        raise SceneServiceError("Entity is not a player character in this campaign")

    await set_pc_present_in_scene(db, pc, present=True, commit=False)

    if state is None:
        state = load_scene_state(scene)
    await _append_pc_to_pbp_initiative_if_needed(db, scene, pc, state)
    save_scene_state(scene, state)
    return state


async def mark_all_campaign_pcs_present_for_scene(
    db: AsyncSession,
    scene: Scene,
) -> None:
    pcs = (
        await db.scalars(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == scene.campaign_id,
                CampaignEntity.entity_type == "PC",
            )
        )
    ).all()
    if not pcs:
        return

    state = load_scene_state(scene)
    for pc in pcs:
        await _apply_pc_presence_to_scene(db, scene, pc, state=state)
    await db.commit()


async def mark_campaign_players_present_for_scene(
    db: AsyncSession,
    scene: Scene,
    user_ids: list[uuid.UUID],
) -> None:
    if not user_ids:
        return

    state = load_scene_state(scene)
    for user_id in user_ids:
        pc = await db.scalar(
            select(CampaignEntity).where(
                CampaignEntity.campaign_id == scene.campaign_id,
                CampaignEntity.entity_type == "PC",
                CampaignEntity.document["player_binding"]["user_id"].as_string() == str(user_id),
            )
        )
        if pc is not None:
            await _apply_pc_presence_to_scene(db, scene, pc, state=state)
    await db.commit()


async def ensure_player_pc_present_in_scene(
    db: AsyncSession,
    scene: Scene,
    user_id: uuid.UUID,
) -> None:
    await mark_campaign_players_present_for_scene(db, scene, [user_id])


async def add_player_to_scene_presence(
    db: AsyncSession,
    scene: Scene,
    *,
    entity_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> SceneResponse:
    if entity_id is None and user_id is None:
        raise SceneServiceError("entity_id or user_id is required")

    pc: CampaignEntity | None = None
    if entity_id is not None:
        pc = await db.scalar(
            select(CampaignEntity).where(
                CampaignEntity.id == entity_id,
                CampaignEntity.campaign_id == scene.campaign_id,
            )
        )
        if pc is None:
            raise SceneServiceError("Player character not found in campaign")
    else:
        assert user_id is not None
        try:
            pc = await find_pc_by_user(db, scene.campaign_id, user_id)
        except CharacterSheetError as exc:
            raise SceneServiceError(str(exc)) from exc
        if pc is None:
            raise SceneServiceError("Player character not found in campaign")

    await _apply_pc_presence_to_scene(db, scene, pc)
    await db.commit()
    await db.refresh(scene)
    response = scene_to_response(scene)

    from app.services.scene_ws import scene_ws_manager

    await scene_ws_manager.broadcast(
        str(scene.id),
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


def _remove_player_from_scene_state(
    state: SceneState,
    *,
    user_id: str,
    entity_id: str | None,
) -> bool:
    """Strip a departed member from live scene tracks without touching chat history."""
    changed = False
    user_id = str(user_id)

    if user_id in state.turn_management.turn_order:
        state.turn_management.turn_order = [
            uid for uid in state.turn_management.turn_order if str(uid) != user_id
        ]
        changed = True
    if str(state.turn_management.current_turn_player_id or "") == user_id:
        state.turn_management.current_turn_player_id = (
            state.turn_management.turn_order[0]
            if state.turn_management.turn_order
            else None
        )
        changed = True

    if entity_id:
        entity_id = str(entity_id)
        original_len = len(state.combat.initiative_order)
        state.combat.initiative_order = [
            entry
            for entry in state.combat.initiative_order
            if str(entry.entity_id) != entity_id
        ]
        if len(state.combat.initiative_order) != original_len:
            changed = True
        if str(state.combat.current_turn_entity_id or "") == entity_id:
            state.combat.current_turn_entity_id = (
                state.combat.initiative_order[0].entity_id
                if state.combat.initiative_order
                else None
            )
            changed = True

        original_refs = len(state.context.prepared_entity_refs)
        state.context.prepared_entity_refs = [
            ref
            for ref in state.context.prepared_entity_refs
            if str(ref.entity_id) != entity_id
        ]
        if len(state.context.prepared_entity_refs) != original_refs:
            changed = True

    return changed


async def remove_player_from_open_scenes(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    pc: CampaignEntity | None = None,
    commit: bool = True,
) -> list[Scene]:
    """Remove a departed member from all ACTIVE/PAUSED scene live state."""
    from app.services.entities import deactivate_pc_player_binding, find_pc_by_user

    user_id_str = str(user_id)
    if pc is None:
        try:
            pc = await find_pc_by_user(db, campaign_id, user_id)
        except CharacterSheetError:
            pc = None

    entity_id = str(pc.id) if pc is not None else None

    scenes = (
        await db.scalars(
            select(Scene).where(
                Scene.campaign_id == campaign_id,
                Scene.status.in_(("ACTIVE", "PAUSED")),
            )
        )
    ).all()

    changed_scenes: list[Scene] = []
    for scene in scenes:
        state = load_scene_state(scene)
        changed = _remove_player_from_scene_state(
            state,
            user_id=user_id_str,
            entity_id=entity_id,
        )
        if changed:
            if state.combat.initiative_order:
                await sync_turn_management_from_initiative(db, campaign_id, state)
            save_scene_state(scene, state)
            changed_scenes.append(scene)

    if pc is not None:
        await deactivate_pc_player_binding(db, pc, commit=False)

    if commit and (changed_scenes or pc is not None):
        await db.commit()
        for scene in changed_scenes:
            await db.refresh(scene)
        if pc is not None:
            await db.refresh(pc)

    return changed_scenes

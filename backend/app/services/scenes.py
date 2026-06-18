import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignEntity, MemoryDocumentType, Scene
from app.schemas.scene import (
    ChatMessage,
    CombatState,
    DiceRollRequest,
    InitiativeEntry,
    MemorySettings,
    NpcPresenceEntry,
    PostMessageRequest,
    SceneContext,
    SceneCreate,
    SceneMetadata,
    ScenePresenceUpdate,
    SceneResponse,
    SceneState,
    SceneStatusType,
    SceneTurnManagementUpdate,
    StateFlags,
    TurnManagement,
)
from app.services.dice import roll_dice as roll_dice_expression
from app.services.combat_parser import try_parse_combat_command
from app.services.combat_resolver import CombatResolverError, entity_display_name, execute_combat_command
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
INTERACTIVE_SCENE_STATUSES = {"ACTIVE"}
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
        normalized.append(entry)
    return normalized


def is_flat_scene_state(data: dict) -> bool:
    return "metadata" not in data and "campaign_id" in data


def _coerce_memory_settings(raw: object) -> dict:
    if isinstance(raw, dict):
        return {
            "max_chat_buffer_size": raw.get("max_chat_buffer_size", 20),
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
        if isinstance(context, dict) and "hidden_npc_ids" not in context:
            context["hidden_npc_ids"] = []
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


def ensure_scene_interactive(scene: Scene) -> None:
    status = scene.status
    if status not in INTERACTIVE_SCENE_STATUSES:
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
) -> SceneState:
    return SceneState(
        metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
        context=SceneContext(scene_objective=scene_objective),
        turn_management=TurnManagement(
            turn_order=turn_order,
            current_turn_player_id=turn_order[0] if turn_order else None,
        ),
    )


def scene_to_response(scene: Scene) -> SceneResponse:
    state = load_scene_state(scene)
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


async def _next_scene_number(db: AsyncSession, campaign_id: uuid.UUID) -> int:
    current_max = await db.scalar(
        select(func.coalesce(func.max(Scene.scene_number), 0)).where(Scene.campaign_id == campaign_id)
    )
    return int(current_max or 0) + 1


def _normalize_display_name(display_name: str | None) -> str | None:
    if display_name is None:
        return None
    trimmed = display_name.strip()
    return trimmed or None


def _build_narrative_text(state: SceneState, *, last_n: int | None = None) -> str:
    lines: list[str] = []
    for message in state.chat_buffer:
        if message.type not in NARRATIVE_MESSAGE_TYPES:
            continue
        text = (message.text or "").strip()
        if text:
            lines.append(text)
    if last_n is not None and last_n > 0:
        lines = lines[-last_n:]
    return "\n".join(lines)


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
) -> str:
    narrative = _build_narrative_text(state)
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
        _build_narrative_text(state, last_n=FALLBACK_SUMMARY_MESSAGE_COUNT),
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
    if len(state.chat_buffer) == original_len:
        raise SceneServiceError("Message not found")

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def list_campaign_scenes(db: AsyncSession, campaign_id: uuid.UUID) -> list[SceneResponse]:
    scenes = (
        await db.scalars(
            select(Scene)
            .where(Scene.campaign_id == campaign_id)
            .order_by(Scene.scene_number.asc())
        )
    ).all()
    return [scene_to_response(scene) for scene in scenes]


async def get_active_scene(db: AsyncSession, campaign_id: uuid.UUID) -> Scene | None:
    return await db.scalar(
        select(Scene)
        .where(Scene.campaign_id == campaign_id, Scene.status == "ACTIVE")
        .order_by(Scene.updated_at.desc(), Scene.created_at.desc())
        .limit(1)
    )


async def pause_other_active_scenes(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    except_scene_id: uuid.UUID | None = None,
) -> list[Scene]:
    query = select(Scene).where(
        Scene.campaign_id == campaign_id,
        Scene.status == "ACTIVE",
    )
    if except_scene_id is not None:
        query = query.where(Scene.id != except_scene_id)

    scenes = (await db.scalars(query)).all()
    for other in scenes:
        state = load_scene_state(other)
        state.metadata.status = "PAUSED"
        save_scene_state(other, state)
    return list(scenes)


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

    await pause_other_active_scenes(db, campaign_id)

    turn_order = payload.turn_order or [str(creator_user_id)]
    scene_state = default_scene_state(
        str(campaign_id),
        turn_order=turn_order,
        scene_objective=payload.scene_objective,
    )
    scene_number = await _next_scene_number(db, campaign_id)
    display_name = _normalize_display_name(payload.display_name)

    scene = Scene(
        campaign_id=campaign_id,
        scene_number=scene_number,
        display_name=display_name,
        status="ACTIVE",
        scene_state=scene_state.model_dump(),
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

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
    ensure_scene_interactive(scene)

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

    combat_command = try_parse_combat_command(payload.text)
    if combat_command is not None:
        try:
            campaign = await get_campaign_or_error(db, scene.campaign_id)
        except CharacterSheetError as exc:
            raise SceneServiceError(str(exc)) from exc
        try:
            combat_result = await execute_combat_command(
                db,
                campaign,
                state,
                sender_id=sender_id,
                sender_role=sender_role,
                command=combat_command,
            )
        except CombatResolverError as exc:
            raise SceneServiceError(str(exc)) from exc

        for combat_message in combat_result.messages:
            state.chat_buffer.append(ChatMessage.model_validate(combat_message))
        state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]
        save_scene_state(scene, state)
        await db.commit()
        await db.refresh(scene)

        for combat_message in combat_result.messages:
            await rag_service.index_message(
                db,
                campaign_id=state.metadata.campaign_id,
                document_id=combat_message["id"],
                text=combat_message.get("text") or payload.text,
                metadata={
                    "scene_id": str(scene.id),
                    "sender_id": sender_id,
                    "type": combat_message.get("type", "COMBAT"),
                },
            )
        return scene_to_response(scene)

    message = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "sender_id": sender_id,
        "type": msg_type,
        "text": payload.text,
        "read_by": [sender_id],
        **speaker_fields,
    }
    state.chat_buffer.append(ChatMessage.model_validate(message))
    trimmed = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]
    state.chat_buffer = trimmed

    if sender_role != "MASTER" and msg_type in NARRATIVE_MESSAGE_TYPES:
        advance_pbp_turn(state)
        if state.combat.initiative_order:
            await sync_turn_management_from_initiative(db, scene.campaign_id, state)

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)

    await rag_service.index_message(
        db,
        campaign_id=state.metadata.campaign_id,
        document_id=message["id"],
        text=payload.text,
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
    ensure_scene_interactive(scene)

    state = load_scene_state(scene)

    try:
        await assert_pbp_post_allowed(
            db, scene.campaign_id, state, sender_id, sender_role
        )
    except PbpTurnError as exc:
        raise SceneServiceError(str(exc)) from exc

    try:
        result = roll_dice_expression(payload.dice_expression, payload.modifier)
    except ValueError as exc:
        raise SceneServiceError(str(exc)) from exc

    message = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "sender_id": sender_id,
        "type": "DICE_ROLL",
        "text": f"Roll: {payload.dice_expression} => {result['final_result']}",
        "dice_expression": payload.dice_expression,
        "raw_result": result["raw_result"],
        "final_result": result["final_result"],
        "skill_checked": payload.skill_checked,
        "read_by": [sender_id],
    }
    state.chat_buffer.append(ChatMessage.model_validate(message))
    state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]

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
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def update_scene_status(
    db: AsyncSession,
    scene: Scene,
    status: SceneStatusType,
) -> SceneResponse:
    if status == "ACTIVE":
        await pause_other_active_scenes(db, scene.campaign_id, except_scene_id=scene.id)

    state = load_scene_state(scene)
    state.metadata.status = status
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)

    if status == "ACTIVE":
        await mark_all_campaign_pcs_present_for_scene(db, scene)
        await db.refresh(scene)

    return scene_to_response(scene)


async def start_active_scene(db: AsyncSession, scene: Scene) -> SceneResponse:
    if scene.status == "CLOSED":
        raise SceneServiceError("Cannot activate a closed scene")
    if scene.status == "ACTIVE":
        return scene_to_response(scene)
    return await update_scene_status(db, scene, "ACTIVE")


async def update_scene_display_name(
    db: AsyncSession,
    scene: Scene,
    display_name: str | None,
) -> SceneResponse:
    scene.display_name = _normalize_display_name(display_name)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def close_scene(db: AsyncSession, scene: Scene) -> SceneResponse:
    if scene.status == "CLOSED":
        raise SceneServiceError("Scene is already closed")

    state = load_scene_state(scene)
    summary = await generate_scene_closure_summary(
        state,
        scene_number=scene.scene_number,
        display_name=scene.display_name,
    )
    state.metadata.closure_summary = summary
    state.metadata.status = "CLOSED"
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
    return scene_to_response(scene)


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

    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


def build_dice_roll_message(
    *,
    sender_id: str,
    roll_result: dict[str, Any],
    entity_id: str | None = None,
    skill_checked: str | None = None,
) -> dict[str, Any]:
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
        "raw_result": roll_result.get("raw_result"),
        "final_result": roll_result.get("final_result"),
        "skill_checked": skill_checked,
        "read_by": [sender_id],
    }
    if entity_id:
        message["entity_id"] = entity_id
    if roll_result.get("roll_type"):
        message["roll_type"] = roll_result["roll_type"]
    if roll_result.get("roll_details"):
        message["roll_details"] = roll_result["roll_details"]
    return message


async def append_dice_roll_to_scene(
    db: AsyncSession,
    scene: Scene,
    *,
    sender_id: str,
    roll_result: dict[str, Any],
    entity_id: str | None = None,
    skill_checked: str | None = None,
) -> SceneResponse:
    ensure_scene_interactive(scene)
    state = load_scene_state(scene)
    message = build_dice_roll_message(
        sender_id=sender_id,
        roll_result=roll_result,
        entity_id=entity_id,
        skill_checked=skill_checked,
    )
    state.chat_buffer.append(ChatMessage.model_validate(message))
    state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]
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

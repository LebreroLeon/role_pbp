from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_scene_for_member,
    parse_uuid,
    require_campaign_master,
    require_campaign_member,
    require_player_open_scene,
    scene_service_error_to_http,
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.scene import (
    ChatMessage,
    CombatAttackRequest,
    CombatInitiativeRequest,
    DiceRollRequest,
    LoreAssistRequest,
    LoreAssistResponse,
    MarkReadRequest,
    PostMessageRequest,
    SceneAddPlayerRequest,
    SceneCreate,
    ScenePresenceUpdate,
    SceneResponse,
    SceneStatusUpdate,
    SceneTurnManagementUpdate,
    SceneUpdate,
)
from app.services.combat_resolver import CombatResolverError, execute_attack, execute_initiative
from app.services.entities import CharacterSheetError, get_campaign_or_error
from app.services.lore_assist import build_player_lore_response
from app.services.scene_ws import scene_ws_manager
from app.services.scenes import (
    SceneServiceError,
    add_player_to_scene_presence,
    close_scene,
    create_scene,
    delete_scene_message,
    ensure_player_pc_present_in_scene,
    load_scene_state,
    mark_messages_read,
    post_message,
    roll_scene_dice,
    save_scene_state,
    scene_to_response,
    start_active_scene,
    update_scene_display_name,
    update_scene_npc_presence,
    update_scene_status,
    update_scene_turn_management,
    advance_scene_pbp_turn,
)

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("", response_model=SceneResponse, status_code=201)
async def create_scene_route(
    payload: SceneCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    campaign_id = parse_uuid(payload.campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_id)

    try:
        response = await create_scene(db, campaign_id, payload, current_user.id)
        await scene_ws_manager.broadcast(
            response.id,
            {"event": "scene_update", "scene": response.model_dump(mode="json")},
        )
        return response
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene_route(
    scene_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_player_open_scene(db, current_user, scene)
    if scene.status == "ACTIVE":
        await ensure_player_pc_present_in_scene(db, scene, current_user.id)
    return scene_to_response(scene)


@router.post("/{scene_id}/messages", response_model=SceneResponse)
async def post_message_route(
    scene_id: str,
    payload: PostMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_player_open_scene(db, current_user, scene)
    role = await require_campaign_member(db, current_user, scene.campaign_id)
    try:
        response = await post_message(db, scene, str(current_user.id), payload, sender_role=role)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/dice", response_model=SceneResponse)
async def roll_scene_dice_route(
    scene_id: str,
    payload: DiceRollRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_player_open_scene(db, current_user, scene)
    role = await require_campaign_member(db, current_user, scene.campaign_id)
    try:
        response = await roll_scene_dice(db, scene, str(current_user.id), payload, sender_role=role)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/read", response_model=SceneResponse)
async def mark_read_route(
    scene_id: str,
    payload: MarkReadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_player_open_scene(db, current_user, scene)
    response = await mark_messages_read(
        db,
        scene,
        str(current_user.id),
        payload.message_ids,
    )
    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/activate", response_model=SceneResponse)
async def activate_scene_route(
    scene_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    try:
        response = await start_active_scene(db, scene)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.patch("/{scene_id}/status", response_model=SceneResponse)
async def patch_scene_status_route(
    scene_id: str,
    payload: SceneStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    if payload.status == "CLOSED":
        raise scene_service_error_to_http(SceneServiceError("Use POST /scenes/{id}/close to close a scene"))
    response = await update_scene_status(db, scene, payload.status)
    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.patch("/{scene_id}", response_model=SceneResponse)
async def patch_scene_route(
    scene_id: str,
    payload: SceneUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    response = await update_scene_display_name(db, scene, payload.display_name)
    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.delete("/{scene_id}/messages/{message_id}", response_model=SceneResponse)
async def delete_scene_message_route(
    scene_id: str,
    message_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    try:
        response = await delete_scene_message(db, scene, message_id)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/close", response_model=SceneResponse)
async def close_scene_route(
    scene_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    try:
        response = await close_scene(db, scene)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


async def _presence_route(
    scene_id: str,
    payload: ScenePresenceUpdate,
    current_user: User,
    db: AsyncSession,
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    try:
        response = await update_scene_npc_presence(db, scene, payload)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/presence", response_model=SceneResponse)
async def post_scene_presence_route(
    scene_id: str,
    payload: ScenePresenceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    return await _presence_route(scene_id, payload, current_user, db)


@router.patch("/{scene_id}/presence", response_model=SceneResponse)
async def patch_scene_presence_route(
    scene_id: str,
    payload: ScenePresenceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    return await _presence_route(scene_id, payload, current_user, db)


@router.post("/{scene_id}/presence/add-player", response_model=SceneResponse)
async def add_player_to_scene_presence_route(
    scene_id: str,
    payload: SceneAddPlayerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)

    entity_uuid = parse_uuid(payload.entity_id, "entity_id") if payload.entity_id else None
    user_uuid = parse_uuid(payload.user_id, "user_id") if payload.user_id else None

    try:
        return await add_player_to_scene_presence(
            db,
            scene,
            entity_id=entity_uuid,
            user_id=user_uuid,
        )
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc


async def _append_combat_messages_and_save(
    db: AsyncSession,
    scene,
    state,
    sender_id: str,
    combat_result,
) -> SceneResponse:
    for combat_message in combat_result.messages:
        state.chat_buffer.append(ChatMessage.model_validate(combat_message))
    state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


@router.post("/{scene_id}/lore-assist", response_model=LoreAssistResponse)
async def lore_assist_route(
    scene_id: str,
    payload: LoreAssistRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> LoreAssistResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_player_open_scene(db, current_user, scene)
    try:
        return await build_player_lore_response(db, scene, current_user.id, payload)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc


@router.patch("/{scene_id}/turn-management", response_model=SceneResponse)
async def patch_turn_management_route(
    scene_id: str,
    payload: SceneTurnManagementUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    try:
        response = await update_scene_turn_management(db, scene, payload)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/turn-management/advance", response_model=SceneResponse)
async def advance_turn_management_route(
    scene_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_campaign_master(db, current_user, scene.campaign_id)
    try:
        response = await advance_scene_pbp_turn(db, scene)
    except SceneServiceError as exc:
        raise scene_service_error_to_http(exc) from exc

    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/combat/initiative", response_model=SceneResponse)
async def roll_combat_initiative_route(
    scene_id: str,
    payload: CombatInitiativeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    role = await require_campaign_member(db, current_user, scene.campaign_id)
    if role != "MASTER":
        raise scene_service_error_to_http(SceneServiceError("Master role required"))

    try:
        campaign = await get_campaign_or_error(db, scene.campaign_id)
    except CharacterSheetError as exc:
        raise scene_service_error_to_http(SceneServiceError(str(exc))) from exc

    state = load_scene_state(scene)
    try:
        combat_result = await execute_initiative(
            db,
            campaign,
            state,
            sender_id=str(current_user.id),
            sender_role=role,
            activate_combat=payload.activate_combat,
        )
    except CombatResolverError as exc:
        raise scene_service_error_to_http(SceneServiceError(str(exc))) from exc

    response = await _append_combat_messages_and_save(
        db, scene, state, str(current_user.id), combat_result
    )
    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response


@router.post("/{scene_id}/combat/attack", response_model=SceneResponse)
async def combat_attack_route(
    scene_id: str,
    payload: CombatAttackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    scene = await get_scene_for_member(db, current_user, parse_uuid(scene_id, "scene_id"))
    await require_player_open_scene(db, current_user, scene)
    role = await require_campaign_member(db, current_user, scene.campaign_id)

    try:
        campaign = await get_campaign_or_error(db, scene.campaign_id)
    except CharacterSheetError as exc:
        raise scene_service_error_to_http(SceneServiceError(str(exc))) from exc

    state = load_scene_state(scene)
    try:
        combat_result = await execute_attack(
            db,
            campaign,
            state,
            sender_id=str(current_user.id),
            sender_role=role,
            attacker_ref=payload.attacker_ref,
            defender_ref=payload.defender_ref,
            weapon_name=payload.weapon_name,
            attack_index=payload.attack_index,
        )
    except CombatResolverError as exc:
        raise scene_service_error_to_http(SceneServiceError(str(exc))) from exc

    response = await _append_combat_messages_and_save(
        db, scene, state, str(current_user.id), combat_result
    )
    await scene_ws_manager.broadcast(
        scene_id,
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response

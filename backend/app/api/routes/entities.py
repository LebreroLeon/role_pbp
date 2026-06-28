import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    parse_uuid,
    require_campaign_master,
    require_campaign_member,
)
from app.core.database import get_db
from app.models.campaign import CampaignEntity
from app.models.user import User
from datetime import UTC, datetime

from app.schemas.entities import EntityCreate, EntityImportItem, EntityImportRequest, EntityImportResponse, EntityPresencePatch, EntityResponse, EntityType, EntityUpdate, EntityExportResponse, ContextualRollRequest
from app.services.entities import (
    CharacterSheetError,
    EntityReferenceError,
    EntityValidationError,
    ensure_single_arc_manifest,
    get_effective_unknown_npc_ids,
    get_campaign_or_error,
    mask_hidden_npc_document,
    npc_player_visibility,
    npc_world_hidden_from_players,
    normalize_entity_document_for_campaign,
    roll_entity_contextual,
    set_pc_present_in_scene,
    strip_master_secrets,
    resolve_entity_cross_references,
    validate_entity_cross_references,
    validate_entity_document,
)
from app.services.entity_avatars import (
    EntityAvatarError,
    clear_entity_avatar_file,
    resolve_entity_avatar_storage,
    save_entity_avatar_file,
)
from app.services.entity_illustrations import (
    EntityIllustrationError,
    clear_entity_illustration_file,
    player_can_view_entity_illustration,
    resolve_entity_illustration_storage,
    save_entity_illustration_file,
)
from app.services.object_storage import StorageNotFoundError, get_storage_backend

router = APIRouter(prefix="/entities", tags=["entities"])


def _entity_to_response(
    entity: CampaignEntity,
    *,
    include_secrets: bool,
    unknown_npc_ids: set[str] | None = None,
    warnings: list[str] | None = None,
) -> EntityResponse:
    document = entity.document
    if not include_secrets:
        document = strip_master_secrets(document, EntityType(entity.entity_type))
        if entity.entity_type == EntityType.NPC.value and (
            (unknown_npc_ids and str(entity.id) in unknown_npc_ids)
            or npc_player_visibility(document) == "unknown"
        ):
            document = mask_hidden_npc_document(document)

    return EntityResponse(
        id=str(entity.id),
        campaign_id=str(entity.campaign_id),
        entity_type=EntityType(entity.entity_type),
        document=document,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        warnings=warnings or [],
    )


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(
    payload: EntityCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    campaign_id = parse_uuid(payload.campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_id)
    campaign = await get_campaign_or_error(db, campaign_id)

    try:
        await ensure_single_arc_manifest(db, campaign_id=campaign_id, entity_type=payload.entity_type)
        document = normalize_entity_document_for_campaign(
            campaign_game_system=campaign.game_system,
            entity_type=payload.entity_type,
            document=payload.document,
        )
        validated = validate_entity_document(payload.entity_type, document)
        await validate_entity_cross_references(
            db,
            campaign_id=campaign_id,
            entity_type=payload.entity_type,
            document=validated.model_dump(mode="json"),
        )
    except EntityReferenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EntityValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    entity = CampaignEntity(
        campaign_id=campaign_id,
        entity_type=payload.entity_type.value,
        document=validated.model_dump(mode="json"),
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return _entity_to_response(entity, include_secrets=True)


@router.get("", response_model=list[EntityResponse])
async def list_entities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    campaign_id: str = Query(...),
    entity_type: EntityType | None = Query(None),
) -> list[EntityResponse]:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    role = await require_campaign_member(db, current_user, campaign_uuid)
    include_secrets = role == "MASTER"
    unknown_npc_ids: set[str] = set()
    if not include_secrets:
        unknown_npc_ids = await get_effective_unknown_npc_ids(db, campaign_uuid)

    query = select(CampaignEntity).where(CampaignEntity.campaign_id == campaign_uuid)
    if entity_type is not None:
        query = query.where(CampaignEntity.entity_type == entity_type.value)

    entities = (await db.scalars(query.order_by(CampaignEntity.created_at))).all()
    if not include_secrets:
        entities = [
            entity
            for entity in entities
            if not (entity.entity_type == EntityType.NPC.value and npc_world_hidden_from_players(entity.document))
        ]
    return [
        _entity_to_response(entity, include_secrets=include_secrets, unknown_npc_ids=unknown_npc_ids)
        for entity in entities
    ]


@router.get("/export", response_model=EntityExportResponse)
async def export_entities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    campaign_id: str = Query(...),
) -> EntityExportResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_uuid)

    entities = (
        await db.scalars(
            select(CampaignEntity)
            .where(CampaignEntity.campaign_id == campaign_uuid)
            .order_by(CampaignEntity.created_at)
        )
    ).all()

    return EntityExportResponse(
        campaign_id=campaign_id,
        exported_at=datetime.now(UTC),
        entities=[
            EntityImportItem(entity_type=EntityType(entity.entity_type), document=entity.document)
            for entity in entities
        ],
    )


@router.post("/import", response_model=EntityImportResponse, status_code=201)
async def import_entities(
    payload: EntityImportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EntityImportResponse:
    campaign_uuid = parse_uuid(payload.campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_uuid)
    campaign = await get_campaign_or_error(db, campaign_uuid)

    created_entities: list[CampaignEntity] = []
    for item in payload.entities:
        try:
            document = normalize_entity_document_for_campaign(
                campaign_game_system=campaign.game_system,
                entity_type=item.entity_type,
                document=item.document,
            )
            validated = validate_entity_document(item.entity_type, document)
        except EntityValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        entity = CampaignEntity(
            campaign_id=campaign_uuid,
            entity_type=item.entity_type.value,
            document=validated.model_dump(mode="json"),
        )
        db.add(entity)
        created_entities.append(entity)

    await db.commit()
    for entity in created_entities:
        await db.refresh(entity)

    return EntityImportResponse(
        created=len(created_entities),
        entities=[_entity_to_response(entity, include_secrets=True) for entity in created_entities],
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    entity = await _get_entity_or_404(entity_id, db)
    role = await require_campaign_member(db, current_user, entity.campaign_id)
    include_secrets = role == "MASTER"
    unknown_npc_ids: set[str] = set()
    if not include_secrets:
        unknown_npc_ids = await get_effective_unknown_npc_ids(db, entity.campaign_id)
        if entity.entity_type == EntityType.NPC.value and npc_world_hidden_from_players(entity.document):
            raise HTTPException(status_code=404, detail="Entity not found")
    return _entity_to_response(
        entity,
        include_secrets=include_secrets,
        unknown_npc_ids=unknown_npc_ids,
    )


@router.patch("/{entity_id}/presence", response_model=EntityResponse)
async def patch_entity_presence(
    entity_id: str,
    payload: EntityPresencePatch,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    entity = await _get_entity_or_404(entity_id, db)
    role = await require_campaign_member(db, current_user, entity.campaign_id)

    if entity.entity_type != EntityType.PC.value:
        raise HTTPException(status_code=400, detail="Only player characters support scene presence")

    if role != "MASTER":
        binding = entity.document.get("player_binding", {})
        if not isinstance(binding, dict) or binding.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="You can only update your own character presence")

    try:
        updated = await set_pc_present_in_scene(
            db,
            entity,
            present=payload.is_present_in_scene,
        )
    except CharacterSheetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _entity_to_response(updated, include_secrets=role == "MASTER")


@router.post("/{entity_id}/roll")
async def roll_entity_sheet(
    entity_id: str,
    payload: ContextualRollRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    entity = await _get_entity_or_404(entity_id, db)
    role = await require_campaign_member(db, current_user, entity.campaign_id)

    try:
        roll_result, scene_id = await roll_entity_contextual(
            db,
            entity=entity,
            sender_id=str(current_user.id),
            sender_role=role,
            roll_type=payload.roll_type,
            dice_expression=payload.dice_expression,
            modifier=payload.modifier,
            context=payload.context,
            master_only=payload.master_only,
        )
    except (CharacterSheetError, EntityValidationError) as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail) from exc
        if "only the master" in detail.lower() or "only roll for your own" in detail.lower():
            raise HTTPException(status_code=403, detail=detail) from exc
        raise HTTPException(status_code=422, detail=detail) from exc

    if scene_id is not None:
        from app.services.scenes import get_scene_by_id

        scene = await get_scene_by_id(db, parse_uuid(scene_id, "scene_id"))
        if scene is not None:
            from app.services.scene_ws import broadcast_scene_update

            await broadcast_scene_update(db, scene, requester_role=role)

    return roll_result


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    payload: EntityUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    entity = await _get_entity_or_404(entity_id, db)
    await require_campaign_master(db, current_user, entity.campaign_id)
    campaign = await get_campaign_or_error(db, entity.campaign_id)

    entity_type = EntityType(entity.entity_type)
    try:
        document = normalize_entity_document_for_campaign(
            campaign_game_system=campaign.game_system,
            entity_type=entity_type,
            document=payload.document,
        )
        validated = validate_entity_document(entity_type, document)
        document_json, warnings = await resolve_entity_cross_references(
            db,
            campaign_id=entity.campaign_id,
            entity_type=entity_type,
            document=validated.model_dump(mode="json"),
            entity_id=entity.id,
            existing_document=entity.document,
        )
    except EntityReferenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EntityValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    entity.document = document_json
    await db.commit()
    await db.refresh(entity)
    return _entity_to_response(entity, include_secrets=True, warnings=warnings)


@router.post("/{entity_id}/avatar", response_model=EntityResponse)
async def upload_entity_avatar(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
) -> EntityResponse:
    entity = await _get_entity_or_404(entity_id, db)
    await require_campaign_master(db, current_user, entity.campaign_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    content = await file.read()
    try:
        await save_entity_avatar_file(
            db,
            entity,
            original_name=file.filename,
            content=content,
            mime_type=file.content_type,
        )
    except EntityAvatarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _entity_to_response(entity, include_secrets=True)


@router.get("/{entity_id}/avatar")
async def get_entity_avatar(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Response:
    entity = await _get_entity_or_404(entity_id, db)
    await require_campaign_member(db, current_user, entity.campaign_id)

    resolved = resolve_entity_avatar_storage(entity)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Avatar not found")

    key, media_type = resolved
    try:
        content = get_storage_backend().get_object(key)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Avatar not found") from None

    return Response(content=content, media_type=media_type)


@router.delete("/{entity_id}/avatar", status_code=204)
async def remove_entity_avatar(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    entity = await _get_entity_or_404(entity_id, db)
    await require_campaign_master(db, current_user, entity.campaign_id)
    await clear_entity_avatar_file(db, entity)


@router.post("/{entity_id}/illustration", response_model=EntityResponse)
async def upload_entity_illustration(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
) -> EntityResponse:
    entity = await _get_entity_or_404(entity_id, db)
    await require_campaign_master(db, current_user, entity.campaign_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    content = await file.read()
    try:
        await save_entity_illustration_file(
            db,
            entity,
            original_name=file.filename,
            content=content,
            mime_type=file.content_type,
        )
    except EntityIllustrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _entity_to_response(entity, include_secrets=True)


@router.get("/{entity_id}/illustration")
async def get_entity_illustration(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Response:
    entity = await _get_entity_or_404(entity_id, db)
    role = await require_campaign_member(db, current_user, entity.campaign_id)

    if role != "MASTER" and not player_can_view_entity_illustration(entity):
        raise HTTPException(status_code=404, detail="Illustration not found")

    resolved = resolve_entity_illustration_storage(entity)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Illustration not found")

    key, media_type = resolved
    try:
        content = get_storage_backend().get_object(key)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Illustration not found") from None

    return Response(content=content, media_type=media_type)


@router.delete("/{entity_id}/illustration", status_code=204)
async def remove_entity_illustration(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    entity = await _get_entity_or_404(entity_id, db)
    await require_campaign_master(db, current_user, entity.campaign_id)
    await clear_entity_illustration_file(db, entity)


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    entity = await _get_entity_or_404(entity_id, db)
    await require_campaign_master(db, current_user, entity.campaign_id)
    await db.delete(entity)
    await db.commit()


async def _get_entity_or_404(entity_id: str, db: AsyncSession) -> CampaignEntity:
    entity_uuid = parse_uuid(entity_id, "entity_id")
    entity = await db.scalar(select(CampaignEntity).where(CampaignEntity.id == entity_uuid))
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

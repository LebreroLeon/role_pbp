import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, parse_uuid, require_campaign_master, require_campaign_member
from app.core.database import get_db
from app.models.user import User
from app.schemas.documents import DocumentResponse, DocumentType
from app.services.documents import (
    DocumentServiceError,
    delete_campaign_document,
    get_campaign_document,
    list_campaign_documents,
    resolve_document_path,
    save_campaign_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    campaign_id: str = Query(..., min_length=1),
) -> list[DocumentResponse]:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_member(db, current_user, campaign_uuid)
    return await list_campaign_documents(db, campaign_uuid)


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    campaign_id: str = Form(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    file: UploadFile = File(...),
) -> DocumentResponse:
    campaign_uuid = parse_uuid(campaign_id, "campaign_id")
    await require_campaign_master(db, current_user, campaign_uuid)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    content = await file.read()
    try:
        return await save_campaign_document(
            db,
            campaign_uuid,
            original_name=file.filename,
            content=content,
            mime_type=file.content_type,
            document_type=document_type,
        )
    except DocumentServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    doc_uuid = parse_uuid(document_id, "document_id")
    doc = await get_campaign_document(db, doc_uuid)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    await require_campaign_member(db, current_user, doc.campaign_id)
    path = resolve_document_path(doc)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")

    return FileResponse(path, filename=doc.original_name, media_type=doc.mime_type or "application/octet-stream")


@router.delete("/{document_id}", status_code=204)
async def remove_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    doc_uuid = parse_uuid(document_id, "document_id")
    doc = await get_campaign_document(db, doc_uuid)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    await require_campaign_master(db, current_user, doc.campaign_id)
    await delete_campaign_document(db, doc)

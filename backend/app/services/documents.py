import tempfile
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import CampaignDocument
from app.schemas.documents import DocumentResponse, DocumentType
from app.services.document_indexer import chunk_text, extract_document_text
from app.services.object_storage import document_storage_key, get_storage_backend
from app.services.rag import rag_service

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt", ".json", ".docx", ".zip"}
INDEXABLE_TYPES = {DocumentType.RULES, DocumentType.ADVENTURE}


class DocumentServiceError(ValueError):
    pass


def _safe_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise DocumentServiceError(
            f"Tipo de archivo no permitido. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return suffix


def document_to_response(doc: CampaignDocument) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        campaign_id=str(doc.campaign_id),
        filename=doc.filename,
        original_name=doc.original_name,
        document_type=DocumentType(doc.document_type),
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        created_at=doc.created_at,
    )


async def list_campaign_documents(db: AsyncSession, campaign_id: uuid.UUID) -> list[DocumentResponse]:
    docs = (
        await db.scalars(
            select(CampaignDocument)
            .where(CampaignDocument.campaign_id == campaign_id)
            .order_by(CampaignDocument.created_at.desc())
        )
    ).all()
    return [document_to_response(doc) for doc in docs]


async def save_campaign_document(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    original_name: str,
    content: bytes,
    mime_type: str | None,
    document_type: DocumentType,
) -> DocumentResponse:
    if len(content) > settings.max_upload_bytes:
        raise DocumentServiceError(f"Archivo demasiado grande (máx. {settings.max_upload_bytes // (1024 * 1024)} MB)")

    suffix = _safe_extension(original_name)
    doc_id = uuid.uuid4()
    stored_name = f"{doc_id}{suffix}"
    storage = get_storage_backend()
    key = document_storage_key(campaign_id, doc_id, suffix)
    storage.put_object(key, content, content_type=mime_type)

    record = CampaignDocument(
        id=doc_id,
        campaign_id=campaign_id,
        filename=stored_name,
        original_name=original_name,
        document_type=document_type.value,
        mime_type=mime_type,
        size_bytes=len(content),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    if document_type in INDEXABLE_TYPES:
        await index_campaign_document_content(db, record)

    return document_to_response(record)


async def index_campaign_document_content(db: AsyncSession, doc: CampaignDocument) -> int:
    from app.models.campaign import MemoryDocumentType

    text = _extract_document_text(doc)
    if not text:
        return 0

    memory_type = (
        MemoryDocumentType.RULES
        if doc.document_type == DocumentType.RULES.value
        else MemoryDocumentType.ADVENTURE
    )
    chunks = chunk_text(text)
    return await rag_service.index_text_chunks(
        db,
        campaign_id=str(doc.campaign_id),
        chunks=chunks,
        document_type=memory_type,
        metadata={
            "document_id": str(doc.id),
            "original_name": doc.original_name,
            "source": "campaign_library",
        },
    )


async def get_campaign_document(
    db: AsyncSession, document_id: uuid.UUID
) -> CampaignDocument | None:
    return await db.scalar(select(CampaignDocument).where(CampaignDocument.id == document_id))


def resolve_document_storage_key(doc: CampaignDocument) -> str:
    suffix = Path(doc.filename).suffix.lower()
    return document_storage_key(doc.campaign_id, doc.id, suffix)


def resolve_document_path(doc: CampaignDocument) -> Path:
    """Local filesystem path for a stored document (local backend only)."""
    if settings.storage_backend.strip().lower() != "local":
        raise DocumentServiceError("resolve_document_path is only valid with STORAGE_BACKEND=local")
    return Path(settings.upload_dir) / resolve_document_storage_key(doc)


def get_document_bytes(doc: CampaignDocument) -> bytes:
    storage = get_storage_backend()
    return storage.get_object(resolve_document_storage_key(doc))


def _extract_document_text(doc: CampaignDocument) -> str:
    suffix = Path(doc.filename).suffix.lower()
    if settings.storage_backend.strip().lower() == "local":
        path = resolve_document_path(doc)
        if path.is_file():
            return extract_document_text(path)
        return ""

    content = get_document_bytes(doc)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        return extract_document_text(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


async def delete_campaign_document(db: AsyncSession, doc: CampaignDocument) -> None:
    storage = get_storage_backend()
    key = resolve_document_storage_key(doc)
    if storage.exists(key):
        storage.delete_object(key)
    await rag_service.delete_chunks_by_document_id(
        db,
        campaign_id=str(doc.campaign_id),
        document_id=str(doc.id),
    )
    await db.delete(doc)
    await db.commit()

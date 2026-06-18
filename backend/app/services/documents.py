import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import CampaignDocument
from app.schemas.documents import DocumentResponse, DocumentType
from app.services.document_indexer import chunk_text, extract_document_text
from app.services.rag import rag_service

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt", ".json", ".docx", ".zip"}
INDEXABLE_TYPES = {DocumentType.RULES, DocumentType.ADVENTURE}


class DocumentServiceError(ValueError):
    pass


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


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
    campaign_dir = _upload_root() / str(campaign_id)
    campaign_dir.mkdir(parents=True, exist_ok=True)
    file_path = campaign_dir / stored_name
    file_path.write_bytes(content)

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

    path = resolve_document_path(doc)
    text = extract_document_text(path)
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


def resolve_document_path(doc: CampaignDocument) -> Path:
    return _upload_root() / str(doc.campaign_id) / doc.filename


async def delete_campaign_document(db: AsyncSession, doc: CampaignDocument) -> None:
    path = resolve_document_path(doc)
    if path.exists():
        path.unlink()
    await db.delete(doc)
    await db.commit()

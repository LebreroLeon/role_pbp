from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_manual import SystemManualMemory, SystemManualSource
from app.rules.game_systems import GAME_SYSTEM_PROFILES
from app.services.rag import embed_text


def list_pdfs(system_dir: Path) -> list[Path]:
    if not system_dir.is_dir():
        return []
    return sorted(system_dir.glob("*.pdf"), key=lambda path: path.name.lower())


def chunk_text(
    text: str,
    *,
    chunk_size: int = 2000,
    overlap: int = 200,
    base_metadata: dict | None = None,
) -> list[tuple[str, dict]]:
    """Split text into overlapping chunks (~500-800 tokens by character proxy)."""
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[tuple[str, dict]] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            break_at = normalized.rfind(" ", start, end)
            if break_at > start + chunk_size // 2:
                end = break_at

        content = normalized[start:end].strip()
        if content:
            metadata = dict(base_metadata or {})
            metadata["chunk_index"] = index
            chunks.append((content, metadata))
            index += 1

        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)

    return chunks


def extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    import fitz

    pages: list[tuple[int, str]] = []
    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            pages.append((page_number, page.get_text()))
    return pages


def build_chunks_from_pages(
    pages: list[tuple[int, str]],
    *,
    source_filename: str,
    chunk_size: int = 2000,
    overlap: int = 200,
) -> list[tuple[str, dict]]:
    chunks: list[tuple[str, dict]] = []
    for page_number, page_text in pages:
        page_chunks = chunk_text(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap,
            base_metadata={
                "page": page_number,
                "source_filename": source_filename,
            },
        )
        chunks.extend(page_chunks)
    return chunks


async def fetch_sources_by_system(db: AsyncSession, system_id: str) -> dict[str, SystemManualSource]:
    rows = await db.scalars(select(SystemManualSource).where(SystemManualSource.system_id == system_id))
    return {row.filename: row for row in rows.all()}


def build_manual_status_entries(
    system_id: str,
    *,
    manuals_root: Path,
    sources_by_filename: dict[str, SystemManualSource],
) -> list[dict]:
    system_dir = manuals_root / system_id
    pdfs = list_pdfs(system_dir)
    entries: list[dict] = []
    seen: set[str] = set()

    for pdf in pdfs:
        seen.add(pdf.name)
        source = sources_by_filename.get(pdf.name)
        rel_path = str(pdf.relative_to(manuals_root)).replace("\\", "/")
        entries.append(
            {
                "filename": pdf.name,
                "path": rel_path,
                "indexed": source is not None and source.indexed_at is not None,
                "indexed_at": source.indexed_at if source else None,
                "chunk_count": source.chunk_count if source else 0,
            }
        )

    for filename, source in sorted(sources_by_filename.items()):
        if filename in seen:
            continue
        entries.append(
            {
                "filename": filename,
                "path": source.path,
                "indexed": source.indexed_at is not None,
                "indexed_at": source.indexed_at,
                "chunk_count": source.chunk_count,
            }
        )

    return entries


def validate_system_id(system_id: str) -> None:
    if system_id not in GAME_SYSTEM_PROFILES:
        raise ValueError(f"Unknown system_id: {system_id}")


def utc_now() -> datetime:
    return datetime.now(UTC)


async def index_system_manual_pdf(
    db: AsyncSession,
    *,
    system_id: str,
    pdf_path: Path,
    manuals_root: Path,
    force: bool,
    dry_run: bool,
) -> int:
    rel_path = str(pdf_path.relative_to(manuals_root)).replace("\\", "/")
    filename = pdf_path.name

    source = await db.scalar(
        select(SystemManualSource).where(
            SystemManualSource.system_id == system_id,
            SystemManualSource.filename == filename,
        )
    )

    if source and source.indexed_at is not None and not force:
        return 0

    pages = extract_pdf_pages(pdf_path)
    chunks = build_chunks_from_pages(pages, source_filename=filename)
    if not chunks:
        return 0

    if dry_run:
        return len(chunks)

    if source is None:
        source = SystemManualSource(
            id=uuid.uuid4(),
            system_id=system_id,
            filename=filename,
            path=rel_path,
        )
        db.add(source)
        await db.flush()
    else:
        source.path = rel_path
        await db.execute(delete(SystemManualMemory).where(SystemManualMemory.source_id == source.id))
        await db.commit()

    batch_commit_size = 25
    chunk_count = 0
    pending = 0
    for content, metadata in chunks:
        embedding = await embed_text(content)
        if embedding is None:
            await db.rollback()
            raise RuntimeError("OPENAI_API_KEY not configured")

        db.add(
            SystemManualMemory(
                id=uuid.uuid4(),
                system_id=system_id,
                source_id=source.id,
                content=content,
                embedding=embedding,
                metadata_=metadata,
            )
        )
        chunk_count += 1
        pending += 1
        if pending >= batch_commit_size:
            source.chunk_count = chunk_count
            await db.commit()
            pending = 0

    source.chunk_count = chunk_count
    source.indexed_at = utc_now()
    await db.commit()
    return chunk_count

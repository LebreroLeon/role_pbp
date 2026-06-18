import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import CampaignMemory, MemoryDocumentType
from app.models.semantic_cache import SemanticCache
from app.models.system_manual import SystemManualMemory

SEMANTIC_CACHE_TTL = timedelta(hours=24)


def _semantic_cache_key(campaign_id: str, query: str, snapshot_hash: str = "") -> str:
    normalized = query.strip().lower()
    digest = hashlib.sha256(f"{campaign_id}:{snapshot_hash}:{normalized}".encode()).hexdigest()
    return digest[:64]


async def embed_text(text: str) -> list[float] | None:
    """Generate an embedding vector via OpenAI, or None when no API key is configured."""
    if not settings.openai_api_key:
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.embedding_model,
                "input": text,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload["data"][0]["embedding"]


class RagService:
    async def _lookup_semantic_cache(
        self,
        db: AsyncSession,
        *,
        campaign_id: str,
        cache_key: str,
    ) -> list[str] | None:
        now = datetime.now(UTC)
        row = await db.scalar(
            select(SemanticCache).where(
                SemanticCache.campaign_id == uuid.UUID(campaign_id),
                SemanticCache.cache_key == cache_key,
                SemanticCache.expires_at > now,
            )
        )
        if row is None:
            return None
        chunks = row.response_payload.get("chunks")
        if isinstance(chunks, list):
            return [str(chunk) for chunk in chunks if str(chunk).strip()]
        return None

    async def _store_semantic_cache(
        self,
        db: AsyncSession,
        *,
        campaign_id: str,
        cache_key: str,
        chunks: list[str],
        query_embedding: list[float] | None,
        snapshot_hash: str = "",
    ) -> None:
        expires_at = datetime.now(UTC) + SEMANTIC_CACHE_TTL
        stmt = (
            insert(SemanticCache)
            .values(
                campaign_id=uuid.UUID(campaign_id),
                cache_key=cache_key,
                state_snapshot_hash=snapshot_hash,
                query_embedding=query_embedding,
                response_payload={"chunks": chunks},
                expires_at=expires_at,
            )
            .on_conflict_do_update(
                index_elements=["campaign_id", "cache_key"],
                set_={
                    "response_payload": {"chunks": chunks},
                    "query_embedding": query_embedding,
                    "expires_at": expires_at,
                    "state_snapshot_hash": snapshot_hash,
                },
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def index_message(
        self,
        db: AsyncSession,
        *,
        campaign_id: str,
        document_id: str,
        text: str,
        metadata: dict | None = None,
        document_type: MemoryDocumentType = MemoryDocumentType.CHAT_LOG,
    ) -> None:
        embedding = await embed_text(text)
        if embedding is None:
            return

        stmt = (
            insert(CampaignMemory)
            .values(
                id=uuid.UUID(document_id),
                campaign_id=uuid.UUID(campaign_id),
                document_type=document_type,
                content=text,
                embedding=embedding,
                metadata_=metadata or {},
            )
            .on_conflict_do_update(
                index_elements=[CampaignMemory.id],
                set_={
                    "content": text,
                    "embedding": embedding,
                    "metadata": metadata or {},
                    "document_type": document_type,
                },
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def index_text_chunks(
        self,
        db: AsyncSession,
        *,
        campaign_id: str,
        chunks: list[str],
        document_type: MemoryDocumentType,
        metadata: dict | None = None,
    ) -> int:
        indexed = 0
        base_metadata = metadata or {}
        for index, chunk in enumerate(chunks):
            text = chunk.strip()
            if not text:
                continue
            chunk_id = uuid.uuid4()
            chunk_metadata = {**base_metadata, "chunk_index": index}
            await self.index_message(
                db,
                campaign_id=campaign_id,
                document_id=str(chunk_id),
                text=text,
                metadata=chunk_metadata,
                document_type=document_type,
            )
            indexed += 1
        return indexed

    async def search_system_manuals(
        self,
        db: AsyncSession,
        *,
        game_system: str,
        query: str,
        top_k: int = 2,
    ) -> list[str]:
        query_embedding = await embed_text(query)
        if query_embedding is None:
            return []

        stmt = (
            select(SystemManualMemory.content)
            .where(SystemManualMemory.system_id == game_system)
            .order_by(SystemManualMemory.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        *,
        campaign_id: str,
        query: str,
        top_k: int = 3,
        include_system_manuals: bool = False,
        game_system: str | None = None,
        manual_top_k: int = 2,
        snapshot_hash: str = "",
    ) -> list[str]:
        cache_key = _semantic_cache_key(campaign_id, query, snapshot_hash)
        cached = await self._lookup_semantic_cache(db, campaign_id=campaign_id, cache_key=cache_key)
        if cached is not None:
            return cached

        query_embedding = await embed_text(query)
        if query_embedding is None:
            return []

        stmt = (
            select(CampaignMemory.content)
            .where(CampaignMemory.campaign_id == uuid.UUID(campaign_id))
            .order_by(CampaignMemory.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        result = await db.execute(stmt)
        chunks = list(result.scalars().all())

        if include_system_manuals and game_system:
            manual_chunks = await self.search_system_manuals(
                db,
                game_system=game_system,
                query=query,
                top_k=manual_top_k,
            )
            chunks.extend(manual_chunks)

        if chunks:
            await self._store_semantic_cache(
                db,
                campaign_id=campaign_id,
                cache_key=cache_key,
                chunks=chunks,
                query_embedding=query_embedding,
                snapshot_hash=snapshot_hash,
            )

        return chunks


rag_service = RagService()

import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import CampaignMemory, MemoryDocumentType
from app.models.system_manual import SystemManualMemory


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
    ) -> list[str]:
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

        return chunks


rag_service = RagService()

from pathlib import Path

import chromadb

from app.core.config import settings


class RagService:
    def __init__(self) -> None:
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection("campaign_memory")

    def index_text(self, campaign_id: str, document_id: str, text: str, metadata: dict | None = None) -> None:
        payload = metadata or {}
        payload["campaign_id"] = campaign_id
        self._collection.upsert(
            ids=[document_id],
            documents=[text],
            metadatas=[payload],
        )

    def search(self, campaign_id: str, query: str, top_k: int = 3) -> list[str]:
        if self._collection.count() == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"campaign_id": campaign_id},
        )
        documents = results.get("documents") or [[]]
        return [doc for doc in documents[0] if doc]


rag_service = RagService()

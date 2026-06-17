import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import MemoryDocumentType
from app.services.rag import RagService, embed_text

MOCK_EMBEDDING = [0.1] * 1536


@pytest.mark.asyncio
async def test_embed_text_returns_none_without_api_key():
    with patch("app.services.rag.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        result = await embed_text("hello world")
        assert result is None


@pytest.mark.asyncio
async def test_embed_text_calls_openai_when_key_present():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": MOCK_EMBEDDING}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.services.rag.settings") as mock_settings,
        patch("app.services.rag.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.openai_api_key = "test-key"
        mock_settings.embedding_model = "text-embedding-3-small"
        result = await embed_text("query text")

    assert result == MOCK_EMBEDDING
    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["json"]["input"] == "query text"
    assert call_kwargs["json"]["model"] == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_index_message_skips_without_embedding():
    db = AsyncMock()
    service = RagService()

    with patch("app.services.rag.embed_text", new=AsyncMock(return_value=None)):
        await service.index_message(
            db,
            campaign_id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            text="archived chat line",
        )

    db.execute.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_index_message_persists_with_mock_embedding():
    db = AsyncMock()
    service = RagService()
    campaign_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    with patch("app.services.rag.embed_text", new=AsyncMock(return_value=MOCK_EMBEDDING)):
        await service.index_message(
            db,
            campaign_id=campaign_id,
            document_id=document_id,
            text="The party enters the tavern.",
            metadata={"scene_id": "scene-1", "type": "SPEAK"},
            document_type=MemoryDocumentType.CHAT_LOG,
        )

    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_returns_empty_without_embedding():
    db = AsyncMock()
    service = RagService()

    with patch("app.services.rag.embed_text", new=AsyncMock(return_value=None)):
        results = await service.search(
            db,
            campaign_id=str(uuid.uuid4()),
            query="what happened in the tavern?",
            top_k=3,
        )

    assert results == []
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_returns_content_strings():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        "The party enters the tavern.",
        "A hooded figure watches from the corner.",
    ]
    db.execute = AsyncMock(return_value=mock_result)
    service = RagService()

    with patch("app.services.rag.embed_text", new=AsyncMock(return_value=MOCK_EMBEDDING)):
        results = await service.search(
            db,
            campaign_id=str(uuid.uuid4()),
            query="tavern",
            top_k=2,
        )

    assert len(results) == 2
    assert "tavern" in results[0].lower()
    db.execute.assert_awaited_once()

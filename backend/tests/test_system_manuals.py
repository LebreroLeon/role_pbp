import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rag import RagService
from app.services.system_manuals import (
    build_chunks_from_pages,
    build_manual_status_entries,
    chunk_text,
    extract_pdf_pages,
    validate_system_id,
)

MOCK_EMBEDDING = [0.1] * 1536
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestChunkText:
    def test_chunk_text_splits_long_content(self):
        text = "word " * 800
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        assert len(chunks) > 1
        assert all(chunk[1]["chunk_index"] == index for index, chunk in enumerate(chunks))

    def test_build_chunks_from_pages_preserves_page_metadata(self):
        pages = [(1, "Fireball deals damage."), (2, "Strength checks lift objects.")]
        chunks = build_chunks_from_pages(pages, source_filename="manual.pdf", chunk_size=80, overlap=10)
        assert chunks
        assert chunks[0][1]["page"] == 1
        assert chunks[0][1]["source_filename"] == "manual.pdf"


class TestExtractPdfPages:
    def test_extract_pdf_pages_reads_fixture_text(self, tmp_path: Path):
        pdf_path = tmp_path / "sample.pdf"
        sample_text = (FIXTURES_DIR / "sample_manual_text.txt").read_text(encoding="utf-8")

        mock_page_one = MagicMock()
        mock_page_one.get_text.return_value = sample_text[:120]
        mock_page_two = MagicMock()
        mock_page_two.get_text.return_value = sample_text[120:]

        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page_one, mock_page_two]))

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc
        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            pages = extract_pdf_pages(pdf_path)

        assert len(pages) == 2
        assert pages[0][0] == 1
        assert "Fireball" in pages[0][1]


class TestManualStatus:
    def test_build_manual_status_merges_disk_and_db(self, tmp_path: Path):
        system_dir = tmp_path / "dnd5e"
        system_dir.mkdir()
        (system_dir / "manual-del-jugador.pdf").write_bytes(b"%PDF-1.4")

        from app.models.system_manual import SystemManualSource

        source = SystemManualSource(
            id=uuid.uuid4(),
            system_id="dnd5e",
            filename="manual-del-jugador.pdf",
            path="dnd5e/manual-del-jugador.pdf",
            indexed_at=datetime(2026, 1, 1, tzinfo=UTC),
            chunk_count=42,
        )

        entries = build_manual_status_entries(
            "dnd5e",
            manuals_root=tmp_path,
            sources_by_filename={source.filename: source},
        )

        assert len(entries) == 1
        assert entries[0]["filename"] == "manual-del-jugador.pdf"
        assert entries[0]["indexed"] is True
        assert entries[0]["chunk_count"] == 42

    def test_validate_system_id_rejects_unknown(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown system_id"):
            validate_system_id("unknown_system")


def test_search_system_manuals_returns_content():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        "Fireball deals 8d6 fire damage.",
    ]
    db.execute = AsyncMock(return_value=mock_result)
    service = RagService()

    async def run_test():
        with patch("app.services.rag.embed_text", new=AsyncMock(return_value=MOCK_EMBEDDING)):
            return await service.search_system_manuals(
                db,
                game_system="dnd5e",
                query="fireball damage",
                top_k=1,
            )

    results = asyncio.run(run_test())
    assert results == ["Fireball deals 8d6 fire damage."]
    assert db.execute.await_count == 1


def test_search_include_system_manuals_appends_manual_chunks():
    db = AsyncMock()
    campaign_result = MagicMock()
    campaign_result.scalars.return_value.all.return_value = ["Party entered the tavern."]
    manual_result = MagicMock()
    manual_result.scalars.return_value.all.return_value = ["Fireball deals 8d6 fire damage."]
    db.execute = AsyncMock(side_effect=[campaign_result, manual_result])
    service = RagService()

    async def run_test():
        with patch("app.services.rag.embed_text", new=AsyncMock(return_value=MOCK_EMBEDDING)):
            return await service.search(
                db,
                campaign_id=str(uuid.uuid4()),
                query="combat rules",
                top_k=1,
                include_system_manuals=True,
                game_system="dnd5e",
                manual_top_k=1,
            )

    results = asyncio.run(run_test())
    assert len(results) == 2
    assert "tavern" in results[0].lower()
    assert "fireball" in results[1].lower()


def test_index_pdf_dry_run_counts_chunks(tmp_path: Path):
    from app.services.system_manuals import index_system_manual_pdf

    manuals_root = tmp_path
    system_dir = manuals_root / "dnd5e"
    system_dir.mkdir()
    pdf_path = system_dir / "rules.pdf"
    pdf_path.write_bytes(b"%PDF")

    sample_text = (FIXTURES_DIR / "sample_manual_text.txt").read_text(encoding="utf-8")
    pages = [(1, sample_text)]

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=None)

    async def run_test():
        with patch("app.services.system_manuals.extract_pdf_pages", return_value=pages):
            return await index_system_manual_pdf(
                db,
                system_id="dnd5e",
                pdf_path=pdf_path,
                manuals_root=manuals_root,
                force=False,
                dry_run=True,
            )

    chunk_count = asyncio.run(run_test())
    assert chunk_count > 0
    db.commit.assert_not_awaited()

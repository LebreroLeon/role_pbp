from app.services.document_indexer import chunk_text, extract_document_text


def test_chunk_text_splits_long_content():
    text = "word " * 500
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_extract_document_text_reads_txt(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Reglas de la casa", encoding="utf-8")
    assert extract_document_text(file_path) == "Reglas de la casa"

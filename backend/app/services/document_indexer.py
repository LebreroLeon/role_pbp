"""Extract plain text from uploaded campaign documents."""

from pathlib import Path


def chunk_text(text: str, *, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    length = len(normalized)
    while start < length:
        end = min(start + chunk_size, length)
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(0, end - overlap)
    return chunks


def extract_document_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        import fitz

        parts: list[str] = []
        with fitz.open(file_path) as doc:
            for page in doc:
                parts.append(page.get_text("text"))
        return "\n".join(parts).strip()

    if suffix in {".txt", ".md", ".json"}:
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()

    return ""

"""Discover monsters in Spanish Edge PDF manuals via outline, text index, or page scan."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from app.services.system_manuals import extract_pdf_pages

_INDEX_NOISE = re.compile(
    r"^(?:índice|indice|contenido|bestiario|apéndice|apendice|tabla|créditos)\b",
    re.IGNORECASE,
)
_INDEX_ENTRY_DOTS = re.compile(
    r"^(.+?)\s*\.{2,}\s*(\d{1,4})\s*$",
    re.MULTILINE,
)
_INDEX_ENTRY_SPACES = re.compile(
    r"^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9a-záéíóúñ\s\-'.]{2,}?)\s{2,}(\d{1,4})\s*$",
    re.MULTILINE,
)
_STAT_BLOCK_HEADER = re.compile(
    r"^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9 /\-'.]{2,}$",
    re.MULTILINE,
)
_TYPE_LINE = re.compile(
    r"^(?P<creature_type>\w+)\s+(?P<size>pequeñ[oa]|median[oa]|grand[ea]|enorme|gargantuesc[ao]|"
    r"gigante|diminut[oa]|minúscul[oa]|minusc[oa]|colosal),?\s*(?P<alignment>.+)$",
    re.MULTILINE | re.IGNORECASE,
)


@dataclass(frozen=True)
class MonsterIndexEntry:
    name: str
    page: int
    source: str  # outline | text_index | page_scan


def _normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().upper())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _slug_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[\s_]+", "-", without_accents)


def extract_pdf_outline(pdf_path: Path) -> list[MonsterIndexEntry]:
    """Read PDF bookmarks / table of contents."""
    import fitz

    entries: list[MonsterIndexEntry] = []
    with fitz.open(pdf_path) as document:
        for level, title, page in document.get_toc(simple=True):
            if level < 1 or not title or not isinstance(page, int) or page < 1:
                continue
            cleaned = " ".join(title.split())
            if _INDEX_NOISE.search(cleaned):
                continue
            if len(cleaned) < 3:
                continue
            entries.append(MonsterIndexEntry(name=cleaned, page=page, source="outline"))
    return _dedupe_entries(entries)


def _dedupe_entries(entries: list[MonsterIndexEntry]) -> list[MonsterIndexEntry]:
    seen: set[tuple[str, int]] = set()
    result: list[MonsterIndexEntry] = []
    for entry in entries:
        key = (_normalize_name(entry.name), entry.page)
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result


def parse_text_index_pages(pages: dict[int, str]) -> list[MonsterIndexEntry]:
    """Parse alphabetical index pages (name .... page)."""
    entries: list[MonsterIndexEntry] = []
    for page_num in sorted(pages):
        text = pages[page_num]
        if not re.search(r"\b(?:índice|indice)\b", text, re.IGNORECASE):
            continue
        for pattern in (_INDEX_ENTRY_DOTS, _INDEX_ENTRY_SPACES):
            for match in pattern.finditer(text):
                name = " ".join(match.group(1).split())
                page = int(match.group(2))
                if len(name) < 3 or page < 1:
                    continue
                if _INDEX_NOISE.search(name):
                    continue
                entries.append(MonsterIndexEntry(name=name, page=page, source="text_index"))
    return _dedupe_entries(entries)


def scan_stat_blocks_in_pages(pages: dict[int, str]) -> list[MonsterIndexEntry]:
    """Fallback: detect stat block headers paired with type lines on each page."""
    entries: list[MonsterIndexEntry] = []
    for page_num in sorted(pages):
        text = pages[page_num]
        type_matches = list(_TYPE_LINE.finditer(text))
        if not type_matches:
            continue
        headers = list(_STAT_BLOCK_HEADER.finditer(text))
        for type_match in type_matches:
            prefix = text[: type_match.start()]
            header_matches = [match for match in headers if match.start() < type_match.start()]
            if not header_matches:
                continue
            header = header_matches[-1].group(0).strip()
            if header.isupper() and len(header) >= 3:
                entries.append(
                    MonsterIndexEntry(name=header.title() if header.isupper() else header, page=page_num, source="page_scan")
                )
    return _dedupe_entries(entries)


def build_monster_index(pdf_path: Path) -> list[MonsterIndexEntry]:
    """Build the best available monster index for a PDF manual."""
    outline = extract_pdf_outline(pdf_path)
    if len(outline) >= 20:
        return outline

    pages = dict(extract_pdf_pages(pdf_path))
    text_index = parse_text_index_pages(pages)
    if len(text_index) >= 20:
        return text_index

    scanned = scan_stat_blocks_in_pages(pages)
    combined = _dedupe_entries(outline + text_index + scanned)
    return combined


def resolve_index_entry(index: list[MonsterIndexEntry], monster_name: str) -> MonsterIndexEntry | None:
    target = _normalize_name(monster_name)
    exact = [entry for entry in index if _normalize_name(entry.name) == target]
    if exact:
        return exact[0]

    partial = [entry for entry in index if target in _normalize_name(entry.name)]
    if len(partial) == 1:
        return partial[0]
    return None


def index_entry_slug(entry: MonsterIndexEntry, *, suffix: str) -> str:
    return f"{_slug_name(entry.name)}-{suffix}"

"""Optional startup seeding of system rulebook PDFs into vector memory."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.system_manual import SystemManualMemory
from app.rules.game_systems import GAME_SYSTEM_PROFILES
from app.services.system_manuals import fetch_sources_by_system, index_system_manual_pdf, list_pdfs

VALID_SYSTEM_IDS = frozenset(GAME_SYSTEM_PROFILES.keys())


def resolve_manuals_dir(override: str | Path | None = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return Path(settings.system_manuals_dir).expanduser().resolve()


def parse_seed_systems(raw: str | None) -> list[str]:
    if raw and raw.strip():
        systems = [item.strip() for item in raw.split(",") if item.strip()]
    else:
        systems = sorted(VALID_SYSTEM_IDS)

    unknown = [system_id for system_id in systems if system_id not in VALID_SYSTEM_IDS]
    if unknown:
        raise ValueError(f"Unknown system_id(s) in SEED_MANUALS_SYSTEMS: {', '.join(unknown)}")
    return systems


async def system_has_chunks(db: AsyncSession, system_id: str) -> bool:
    count = await db.scalar(
        select(func.count())
        .select_from(SystemManualMemory)
        .where(SystemManualMemory.system_id == system_id)
    )
    return bool(count)


async def scan_system(
    db: AsyncSession,
    system_id: str,
    manuals_root: Path,
    *,
    dry_run: bool,
    force: bool,
    skip_if_indexed: bool,
    log=print,
) -> int:
    system_dir = manuals_root / system_id
    pdfs = list_pdfs(system_dir)

    log(f"\n[{system_id}] {system_dir}")
    if not pdfs:
        log(f"  (sin PDFs — copia manuales según data/manuals/{system_id}/README.md)")
        return 0

    if skip_if_indexed and not force and not dry_run:
        if await system_has_chunks(db, system_id):
            log("  → SKIP (system already has indexed chunks; use SEED_MANUALS=force to reindex)")
            return 0

    total_chunks = 0
    sources = await fetch_sources_by_system(db, system_id)

    for pdf in pdfs:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        log(f"  {pdf.name} ({size_mb:.1f} MB)")

        existing = sources.get(pdf.name)
        if existing and existing.indexed_at is not None and not force and not dry_run:
            log(f"    → SKIP (already indexed, {existing.chunk_count} chunks)")
            continue

        try:
            chunk_count = await index_system_manual_pdf(
                db,
                system_id=system_id,
                pdf_path=pdf,
                manuals_root=manuals_root,
                force=force,
                dry_run=dry_run,
            )
        except RuntimeError as exc:
            log(f"    → ABORT ({exc})")
            return total_chunks

        if dry_run:
            action = f"DRY-RUN ({chunk_count} chunks)" if chunk_count else "SKIP (no text)"
        elif chunk_count == 0:
            action = "SKIP (no extractable text)"
        else:
            action = f"INDEXED ({chunk_count} chunks)"

        log(f"    → {action}")
        total_chunks += chunk_count

    log(f"  Total: {len(pdfs)} PDF(s), {total_chunks} chunk(s) processed.")
    return total_chunks


async def seed_system_manuals(
    *,
    manuals_dir: str | Path | None = None,
    systems: list[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
    skip_if_indexed: bool = True,
    log=print,
) -> int:
    if not settings.openai_api_key.strip():
        log("SEED_MANUALS: skipping — OPENAI_API_KEY not configured.")
        return 0

    manuals_root = resolve_manuals_dir(manuals_dir)
    if not manuals_root.is_dir():
        log(f"SEED_MANUALS: skipping — manuals directory not found: {manuals_root}")
        return 0

    system_ids = systems if systems is not None else parse_seed_systems(settings.seed_manuals_systems)
    total_chunks = 0

    async with SessionLocal() as db:
        for system_id in system_ids:
            total_chunks += await scan_system(
                db,
                system_id,
                manuals_root,
                dry_run=dry_run,
                force=force,
                skip_if_indexed=skip_if_indexed,
                log=log,
            )

    return total_chunks


def seed_system_manuals_if_enabled() -> None:
    """Run after migrations when SEED_MANUALS is true or force. Never raises."""
    mode = settings.seed_manuals_mode
    if mode is None:
        return

    force = mode == "force"
    label = "force reindex" if force else "auto seed"
    print(f"SEED_MANUALS={mode}: starting system manual {label}...")

    try:
        systems = parse_seed_systems(settings.seed_manuals_systems)
    except ValueError as exc:
        print(f"SEED_MANUALS: skipping — {exc}", file=sys.stderr)
        return

    try:
        total = asyncio.run(
            seed_system_manuals(
                force=force,
                systems=systems,
                skip_if_indexed=not force,
            )
        )
        print(f"SEED_MANUALS: finished ({total} chunk(s) processed).")
    except Exception as exc:
        print(f"SEED_MANUALS: skipped due to error (non-fatal): {exc}", file=sys.stderr)

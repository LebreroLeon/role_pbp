"""Close duplicate open scenes (ACTIVE/PAUSED), keeping only one per campaign."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.campaign import Scene
from app.services.scenes import close_other_open_scenes


async def run(*, dry_run: bool) -> int:
    closed_rows: list[tuple[str, str, int | None, str]] = []

    async with SessionLocal() as db:
        duplicate_campaigns = (
            await db.execute(
                select(Scene.campaign_id, func.count())
                .where(Scene.status.in_(("ACTIVE", "PAUSED")))
                .group_by(Scene.campaign_id)
                .having(func.count() > 1)
            )
        ).all()

        for campaign_id, open_count in duplicate_campaigns:
            scenes = (
                await db.scalars(
                    select(Scene)
                    .where(
                        Scene.campaign_id == campaign_id,
                        Scene.status.in_(("ACTIVE", "PAUSED")),
                    )
                    .order_by(Scene.scene_number.desc().nulls_last(), Scene.updated_at.desc())
                )
            ).all()
            keeper = scenes[0]
            closed = await close_other_open_scenes(db, campaign_id, except_scene_id=keeper.id)
            for scene in closed:
                closed_rows.append(
                    (
                        str(campaign_id),
                        str(scene.id),
                        scene.scene_number,
                        str(keeper.id),
                    )
                )

        if dry_run:
            await db.rollback()
        else:
            await db.commit()

    print("=== Duplicate open scenes (ACTIVE/PAUSED) ===")
    if not closed_rows:
        print("No duplicate open scenes found.")
    else:
        for campaign_id, scene_id, scene_number, keeper_id in closed_rows:
            print(
                f"  campaign={campaign_id} | scene #{scene_number} ({scene_id}) "
                f"-> CLOSED (keeper={keeper_id})"
            )

    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n{mode}: closed {len(closed_rows)} scene(s).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Close duplicate open scenes per campaign (keeps highest scene_number)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without committing.",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(dry_run=args.dry_run)))


if __name__ == "__main__":
    main()

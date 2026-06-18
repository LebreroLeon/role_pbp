"""Pause duplicate ACTIVE scenes, keeping only the most recent per campaign."""

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
from app.services.scenes import load_scene_state, save_scene_state


async def run(*, dry_run: bool) -> int:
    paused_rows: list[tuple[str, str, int, str]] = []

    async with SessionLocal() as db:
        duplicate_campaigns = (
            await db.execute(
                select(Scene.campaign_id, func.count())
                .where(Scene.status == "ACTIVE")
                .group_by(Scene.campaign_id)
                .having(func.count() > 1)
            )
        ).all()

        for campaign_id, active_count in duplicate_campaigns:
            scenes = (
                await db.scalars(
                    select(Scene)
                    .where(Scene.campaign_id == campaign_id, Scene.status == "ACTIVE")
                    .order_by(Scene.updated_at.desc(), Scene.created_at.desc())
                )
            ).all()
            keeper = scenes[0]
            for scene in scenes[1:]:
                paused_rows.append(
                    (
                        str(campaign_id),
                        str(scene.id),
                        scene.scene_number,
                        str(keeper.id),
                    )
                )
                if not dry_run:
                    state = load_scene_state(scene)
                    state.metadata.status = "PAUSED"
                    save_scene_state(scene, state)

        if dry_run:
            await db.rollback()
        else:
            await db.commit()

    print("=== Duplicate ACTIVE scenes ===")
    if not paused_rows:
        print("No duplicate ACTIVE scenes found.")
    else:
        for campaign_id, scene_id, scene_number, keeper_id in paused_rows:
            print(
                f"  campaign={campaign_id} | scene #{scene_number} ({scene_id}) "
                f"-> PAUSED (keeper={keeper_id})"
            )

    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n{mode}: paused {len(paused_rows)} scene(s).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pause duplicate ACTIVE scenes per campaign (keeps most recent)."
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

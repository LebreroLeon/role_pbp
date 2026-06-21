"""Run Alembic migrations with legacy-schema bootstrap."""

import asyncio
import subprocess
import sys

from sqlalchemy import text

from app.core.database import create_db_engine


async def legacy_tables_without_alembic() -> bool:
    engine = create_db_engine(echo=False)
    try:
        async with engine.connect() as conn:
            campaigns = (await conn.execute(text("SELECT to_regclass('public.campaigns')"))).scalar()
            alembic = (await conn.execute(text("SELECT to_regclass('public.alembic_version')"))).scalar()
            return campaigns is not None and alembic is None
    finally:
        await engine.dispose()


def run_migrations() -> None:
    if asyncio.run(legacy_tables_without_alembic()):
        print("Legacy schema detected — stamping Alembic head.")
        subprocess.run(["alembic", "stamp", "head"], check=True)

    print("Applying database migrations...")
    result = subprocess.run(["alembic", "upgrade", "head"], check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)

    from app.core.seed_manuals import seed_system_manuals_if_enabled
    from app.core.seed_monsters import seed_monster_catalog_if_enabled

    seed_system_manuals_if_enabled()
    seed_monster_catalog_if_enabled()


if __name__ == "__main__":
    run_migrations()

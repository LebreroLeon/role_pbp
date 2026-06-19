import asyncio
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.seed_manuals import (
    parse_seed_systems,
    seed_system_manuals,
    seed_system_manuals_if_enabled,
    system_has_chunks,
)


class TestParseSeedSystems:
    def test_empty_defaults_to_all_known_systems(self):
        systems = parse_seed_systems("")
        assert "dnd5e" in systems
        assert "vtm_v5" in systems

    def test_comma_separated_list(self):
        assert parse_seed_systems("dnd5e, vtm_v5") == ["dnd5e", "vtm_v5"]

    def test_rejects_unknown_system(self):
        with pytest.raises(ValueError, match="Unknown system_id"):
            parse_seed_systems("not_a_system")


class TestSeedSystemManuals:
    def test_skips_without_openai_key(self, tmp_path: Path):
        logs = StringIO()

        async def run_test():
            with patch("app.core.seed_manuals.settings") as mock_settings:
                mock_settings.openai_api_key = ""
                mock_settings.system_manuals_dir = str(tmp_path)
                mock_settings.seed_manuals_systems = "dnd5e"
                return await seed_system_manuals(
                    manuals_dir=tmp_path,
                    systems=["dnd5e"],
                    log=logs.write,
                )

        assert asyncio.run(run_test()) == 0
        assert "OPENAI_API_KEY not configured" in logs.getvalue()

    def test_skips_when_manuals_dir_missing(self, tmp_path: Path):
        logs = StringIO()
        missing = tmp_path / "missing"

        async def run_test():
            with patch("app.core.seed_manuals.settings") as mock_settings:
                mock_settings.openai_api_key = "sk-test"
                return await seed_system_manuals(
                    manuals_dir=missing,
                    systems=["dnd5e"],
                    log=logs.write,
                )

        assert asyncio.run(run_test()) == 0
        assert "manuals directory not found" in logs.getvalue()

    def test_skips_system_with_existing_chunks(self, tmp_path: Path):
        manuals_root = tmp_path / "manuals"
        system_dir = manuals_root / "dnd5e"
        system_dir.mkdir(parents=True)
        (system_dir / "rules.pdf").write_bytes(b"%PDF")

        logs = StringIO()
        mock_db = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_db
        mock_context.__aexit__.return_value = None
        mock_index = AsyncMock()

        async def run_test():
            with (
                patch("app.core.seed_manuals.settings") as mock_settings,
                patch("app.core.seed_manuals.SessionLocal", return_value=mock_context),
                patch("app.core.seed_manuals.system_has_chunks", new=AsyncMock(return_value=True)),
                patch("app.core.seed_manuals.index_system_manual_pdf", new=mock_index),
            ):
                mock_settings.openai_api_key = "sk-test"
                return await seed_system_manuals(
                    manuals_dir=manuals_root,
                    systems=["dnd5e"],
                    skip_if_indexed=True,
                    log=logs.write,
                )

        assert asyncio.run(run_test()) == 0
        mock_index.assert_not_awaited()
        assert "already has indexed chunks" in logs.getvalue()


class TestSeedSystemManualsIfEnabled:
    def test_no_op_when_disabled(self):
        with patch("app.core.seed_manuals.settings") as mock_settings:
            mock_settings.seed_manuals_mode = None
            with patch("app.core.seed_manuals.asyncio.run") as mock_run:
                seed_system_manuals_if_enabled()
                mock_run.assert_not_called()

    def test_runs_when_enabled(self):
        with patch("app.core.seed_manuals.settings") as mock_settings:
            mock_settings.seed_manuals_mode = "true"
            mock_settings.seed_manuals_systems = "dnd5e"
            with patch("app.core.seed_manuals.asyncio.run", return_value=0) as mock_run:
                seed_system_manuals_if_enabled()
                mock_run.assert_called_once()

    def test_swallows_errors(self):
        with patch("app.core.seed_manuals.settings") as mock_settings:
            mock_settings.seed_manuals_mode = "true"
            mock_settings.seed_manuals_systems = "dnd5e"
            with patch("app.core.seed_manuals.asyncio.run", side_effect=RuntimeError("boom")):
                seed_system_manuals_if_enabled()


def test_system_has_chunks_uses_scalar():
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=3)

    assert asyncio.run(system_has_chunks(db, "dnd5e")) is True
    db.scalar.assert_awaited_once()

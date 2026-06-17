import pytest

from app.rules.base import AttackContext, RollContext
from app.rules.cyberpunk_red.plugin import CyberpunkRedPlugin
from app.rules.cyberpunk_red.schema import CyberpunkRedSheet
from app.rules.registry import get_plugin
from app.rules.vtm_v5.plugin import VtmV5Plugin
from app.rules.vtm_v5.schema import VtmV5Sheet
from app.services import dice as dice_service


@pytest.fixture
def cyberpunk_plugin() -> CyberpunkRedPlugin:
    return CyberpunkRedPlugin()


@pytest.fixture
def vtm_plugin() -> VtmV5Plugin:
    return VtmV5Plugin()


@pytest.fixture
def cyberpunk_sheet() -> dict:
    return CyberpunkRedPlugin().default_pc_sheet()


@pytest.fixture
def vtm_sheet() -> dict:
    return VtmV5Plugin().default_pc_sheet()


class TestCyberpunkSchema:
    def test_validate_default_pc_sheet(self, cyberpunk_plugin: CyberpunkRedPlugin):
        sheet = cyberpunk_plugin.default_pc_sheet()
        validated = cyberpunk_plugin.validate_pc_sheet(sheet)
        assert isinstance(validated, CyberpunkRedSheet)
        assert validated.hp.max == 40
        assert len(validated.weapons) == 1

    def test_registry_returns_cyberpunk_plugin(self):
        plugin = get_plugin("cyberpunk_red")
        assert plugin.system_id == "cyberpunk_red"


class TestCyberpunkRolls:
    def test_skill_check_handgun(self, cyberpunk_plugin: CyberpunkRedPlugin, cyberpunk_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 7)
        result = cyberpunk_plugin.resolve_roll(
            "skill_check",
            cyberpunk_sheet,
            RollContext(skill="handgun", dc=2),
        )
        # REF 6 + handgun 4 = 10 dice, all roll 7 → 10 successes
        assert result.total == 10
        assert result.success is True
        assert result.details["skill"] == "handgun"

    def test_stat_check_ref(self, cyberpunk_plugin: CyberpunkRedPlugin, cyberpunk_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 4)
        result = cyberpunk_plugin.resolve_roll(
            "stat_check",
            cyberpunk_sheet,
            RollContext(ability="ref", dc=1),
        )
        assert result.total == 0
        assert result.success is False

    def test_damage_roll(self, cyberpunk_plugin: CyberpunkRedPlugin, cyberpunk_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 5 if b == 6 else 1)
        result = cyberpunk_plugin.resolve_roll(
            "damage",
            cyberpunk_sheet,
            RollContext(attack_name="Heavy Pistol"),
        )
        assert result.total == 10
        assert result.details["damage_type"] == "ballistic"

    def test_attack_roll_vs_evasion(self, cyberpunk_plugin: CyberpunkRedPlugin, cyberpunk_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 8)
        result = cyberpunk_plugin.resolve_roll(
            "attack_roll",
            cyberpunk_sheet,
            RollContext(skill="handgun", target_ac=3),
        )
        assert result.total == 10
        assert result.success is True

    def test_initiative(self, cyberpunk_plugin: CyberpunkRedPlugin, cyberpunk_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 6 if b == 10 else 1)
        result = cyberpunk_plugin.resolve_roll("initiative", cyberpunk_sheet, RollContext())
        assert result.total == 12  # REF 6 + d10(6)


class TestCyberpunkCombat:
    def _fake_randint(self, a: int, b: int) -> int:
        if b == 10:
            return 8
        if b == 6:
            return 4
        return 4

    def test_resolve_attack_and_apply_damage(
        self,
        cyberpunk_plugin: CyberpunkRedPlugin,
        cyberpunk_sheet: dict,
        monkeypatch,
    ):
        monkeypatch.setattr("random.randint", self._fake_randint)

        defender = cyberpunk_plugin.default_npc_sheet("medium")
        attack = cyberpunk_plugin.resolve_attack(
            cyberpunk_sheet,
            defender,
            "Heavy Pistol",
            AttackContext(),
        )
        assert attack.hit is True
        assert attack.damage is not None

        updated, application = cyberpunk_plugin.apply_damage(defender, attack.damage)
        assert application.hp_before == 40
        assert application.hp_after == 32
        assert updated["hp"]["current"] == 32


class TestVtmSchema:
    def test_validate_default_pc_sheet(self, vtm_plugin: VtmV5Plugin):
        sheet = vtm_plugin.default_pc_sheet()
        validated = vtm_plugin.validate_pc_sheet(sheet)
        assert isinstance(validated, VtmV5Sheet)
        assert validated.hunger == 1

    def test_registry_returns_vtm_plugin(self):
        plugin = get_plugin("vtm_v5")
        assert plugin.system_id == "vtm_v5"


class TestVtmRolls:
    def test_skill_check_with_hunger(self, vtm_plugin: VtmV5Plugin, vtm_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 7)
        result = vtm_plugin.resolve_roll(
            "skill_check",
            vtm_sheet,
            RollContext(skill="athletics", dc=2),
        )
        # DEX 3 + athletics 2 = 5 dice, hunger 1 → 4 regular + 1 hunger, all 7s → 5 successes
        assert result.total == 5
        assert result.success is True
        assert result.details["hunger_dice"] == 1

    def test_attribute_check(self, vtm_plugin: VtmV5Plugin, vtm_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 8)
        result = vtm_plugin.resolve_roll(
            "attribute_check",
            vtm_sheet,
            RollContext(ability="wil", dc=1),
        )
        assert result.total == 3  # WIL 3 dice, all 8s
        assert result.success is True

    def test_rouse_check_success(self, vtm_plugin: VtmV5Plugin, vtm_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 8)
        result = vtm_plugin.resolve_roll("rouse_check", vtm_sheet, RollContext())
        assert result.success is True
        assert result.details["hunger_after"] == 1

    def test_rouse_check_failure(self, vtm_plugin: VtmV5Plugin, vtm_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 3)
        result = vtm_plugin.resolve_roll("rouse_check", vtm_sheet, RollContext())
        assert result.success is False
        assert result.details["hunger_after"] == 2

    def test_discipline_check(self, vtm_plugin: VtmV5Plugin, vtm_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 9)
        result = vtm_plugin.resolve_roll(
            "discipline_check",
            vtm_sheet,
            RollContext(skill="potence", dc=1),
        )
        # WIL 3 + potence 1 = 4 dice, hunger 1 → 3 regular + 1 hunger
        assert result.total == 4
        assert result.success is True

    def test_hunger_complication_on_one(self, vtm_plugin: VtmV5Plugin, vtm_sheet: dict, monkeypatch):
        calls = {"n": 0}

        def fake_randint(_a: int, _b: int) -> int:
            calls["n"] += 1
            return 1 if calls["n"] == 5 else 7

        monkeypatch.setattr("random.randint", fake_randint)
        result = vtm_plugin.resolve_roll(
            "skill_check",
            vtm_sheet,
            RollContext(skill="athletics"),
        )
        assert result.details["hunger_complications"]


class TestDiceDelegation:
    def test_contextual_roll_cyberpunk(self, cyberpunk_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 7)
        payload = dice_service.roll_dice(
            "10d10",
            game_system="cyberpunk_red",
            sheet=cyberpunk_sheet,
            roll_type="skill_check",
            context={"skill": "handgun", "dc": 1},
        )
        assert payload["contextual"] is True
        assert payload["game_system"] == "cyberpunk_red"
        assert payload["success"] is True

    def test_contextual_roll_vtm(self, vtm_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 8)
        payload = dice_service.roll_dice(
            "5d10",
            game_system="vtm_v5",
            sheet=vtm_sheet,
            roll_type="skill_check",
            context={"skill": "athletics", "dc": 1},
        )
        assert payload["contextual"] is True
        assert payload["game_system"] == "vtm_v5"
        assert payload["success"] is True

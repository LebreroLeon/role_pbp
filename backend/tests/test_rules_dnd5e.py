import pytest

from app.rules.dnd5e.plugin import Dnd5ePlugin, ability_modifier
from app.rules.dnd5e.schema import Dnd5eSheet
from app.rules.registry import get_plugin
from app.rules.base import RollContext, AttackContext
from app.services import dice as dice_service


@pytest.fixture
def plugin() -> Dnd5ePlugin:
    return Dnd5ePlugin()


@pytest.fixture
def sample_sheet() -> dict:
    return Dnd5ePlugin().default_pc_sheet()


class TestDnd5eSchema:
    def test_validate_default_pc_sheet(self, plugin: Dnd5ePlugin):
        sheet = plugin.default_pc_sheet()
        validated = plugin.validate_pc_sheet(sheet)
        assert isinstance(validated, Dnd5eSheet)
        assert validated.hp.max == 24
        assert len(validated.attacks) == 1

    def test_ability_modifier(self):
        assert ability_modifier(10) == 0
        assert ability_modifier(14) == 2
        assert ability_modifier(8) == -1


def _fake_randint(a: int, b: int) -> int:
    if b == 20:
        return 16
    if b == 8:
        return 5
    return 4


class TestDnd5eRolls:
    def test_skill_check_perception(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 15 if b == 20 else 1)
        result = plugin.resolve_roll(
            "skill_check",
            sample_sheet,
            RollContext(skill="perception", dc=12),
        )
        # WIS 11 (+0) + proficient (+2) + roll 15 = 17
        assert result.total == 17
        assert result.success is True
        assert result.details["skill"] == "perception"

    def test_saving_throw_dex_proficient(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 10 if b == 20 else 1)
        result = plugin.resolve_roll(
            "saving_throw",
            sample_sheet,
            RollContext(ability="dex"),
        )
        # DEX 12 (+1) + prof (+2) + 10 = 13
        assert result.total == 13

    def test_attack_roll_hit(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 18 if b == 20 else 1)
        result = plugin.resolve_roll(
            "attack_roll",
            sample_sheet,
            RollContext(attack_name="Longsword", target_ac=15),
        )
        assert result.total == 23
        assert result.success is True
        assert result.details["hit"] is True

    def test_attack_roll_miss_natural_one(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 1 if b == 20 else 1)
        result = plugin.resolve_roll(
            "attack_roll",
            sample_sheet,
            RollContext(attack_index=0, target_ac=5),
        )
        assert result.success is False

    def test_damage_roll(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 6 if b == 8 else 10)
        result = plugin.resolve_roll("damage", sample_sheet, RollContext(attack_name="Longsword"))
        assert result.total == 9  # 1d8(6) + 3
        assert result.details["damage_type"] == "slashing"


class TestDiceDelegation:
    def test_contextual_roll_via_dice_service(self, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 12 if b == 20 else 1)
        payload = dice_service.roll_dice(
            "1d20",
            game_system="dnd5e",
            sheet=sample_sheet,
            roll_type="ability_check",
            context={"ability": "str", "dc": 10},
        )
        assert payload["contextual"] is True
        assert payload["game_system"] == "dnd5e"
        # STR 14 (+2) + 12 = 14
        assert payload["final_result"] == 14
        assert payload["success"] is True

    def test_registry_returns_dnd5e_plugin(self):
        plugin = get_plugin("dnd5e")
        assert plugin.system_id == "dnd5e"


class TestDnd5eCombat:
    def test_resolve_attack_and_apply_damage(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", _fake_randint)

        defender = plugin.default_npc_sheet("medium")
        attack = plugin.resolve_attack(
            sample_sheet,
            defender,
            "Longsword",
            AttackContext(target_ac=12),
        )
        assert attack.hit is True
        assert attack.damage is not None
        assert attack.damage.amount == 8  # 1d8(5) + 3

        updated, application = plugin.apply_damage(defender, attack.damage)
        assert application.hp_before == 16
        assert application.hp_after == 8
        assert updated["hp"]["current"] == 8

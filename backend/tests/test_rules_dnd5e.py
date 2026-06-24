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

    def test_validate_frontend_nested_sheet(self, plugin: Dnd5ePlugin):
        sheet = {
            "identity": {"class_level": "Guerrero 3", "background": "", "race": "Humano", "alignment": "LG"},
            "roleplay": {"personality_traits": "", "ideals": "", "bonds": "", "flaws": "", "inspiration": False},
            "features_traits": "",
            "equipment": "",
            "currency": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "proficiency": {
                "bonus": 2,
                "saving_throws": [],
                "skills": [{"name": "Perception", "proficient": False, "expertise": False}],
            },
            "defense": {
                "ac": 10,
                "hp": {"max": 10, "current": 10, "temp": 0},
                "hit_dice": "1d8",
                "death_saves": {"successes": 0, "failures": 0},
            },
            "attacks": [
                {
                    "name": "Ataque desarmado",
                    "ability": "str",
                    "proficient": True,
                    "damage": {"dice": "1d4", "type": "contundente"},
                    "properties": [],
                }
            ],
            "initiative": {"modifier": 0},
            "conditions": [],
        }
        validated = plugin.validate_pc_sheet(sheet)
        assert isinstance(validated, Dnd5eSheet)
        assert validated.identity.class_ == "Guerrero"
        assert validated.identity.level == 3
        assert validated.attacks[0].damage_dice == "1d4"
        assert validated.attacks[0].damage_type == "contundente"
        assert validated.attacks[0].to_hit_bonus == 2

    def test_validate_frontend_nested_sheet_with_spellcasting(self, plugin: Dnd5ePlugin):
        sheet = {
            "identity": {"class_level": "Mago 5", "background": "", "race": "Elfo", "alignment": "CN"},
            "roleplay": {"personality_traits": "", "ideals": "", "bonds": "", "flaws": "", "inspiration": False},
            "features_traits": "Rasgo arcano",
            "other_proficiencies": "Común, Élfico; kit de herboristería",
            "equipment": "",
            "currency": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
            "abilities": {"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
            "proficiency": {
                "bonus": 3,
                "saving_throws": ["int", "wis"],
                "skills": [{"name": "Arcana", "proficient": True, "expertise": False}],
            },
            "defense": {
                "ac": 13,
                "hp": {"max": 28, "current": 28, "temp": 0},
                "hit_dice": "5d6",
                "death_saves": {"successes": 0, "failures": 0},
            },
            "attacks": [
                {
                    "name": "Bastón",
                    "ability": "str",
                    "proficient": False,
                    "damage": {"dice": "1d6", "type": "contundente"},
                    "properties": [],
                }
            ],
            "initiative": {"modifier": 0},
            "conditions": [],
            "spellcasting": {
                "ability": "int",
                "save_dc": 16,
                "attack_bonus": 8,
                "slots": [
                    {"level": 1, "total": 4, "used": 1},
                    {"level": 2, "total": 3, "used": 0},
                    {"level": 3, "total": 2, "used": 0},
                ],
                "spells": [
                    {"name": "Prestidigitación", "level": 0, "prepared": True, "ritual": False, "notes": ""},
                    {"name": "Bola de fuego", "level": 3, "prepared": True, "ritual": False, "notes": "8d6"},
                ],
            },
        }
        validated = plugin.validate_pc_sheet(sheet)
        assert isinstance(validated, Dnd5eSheet)
        assert validated.other_proficiencies == "Común, Élfico; kit de herboristería"
        assert validated.spellcasting.save_dc == 16
        assert validated.spellcasting.spells[1].name == "Bola de fuego"

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
        assert result.details["roll_label"] == "Percepción (Sabiduría)"
        assert result.details["modifier_breakdown"]
        assert "Percepción" in result.chat_summary
        assert "1d20=15" in result.chat_summary

    def test_ability_check_includes_spanish_label(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, b: 12 if b == 20 else 1)
        result = plugin.resolve_roll(
            "ability_check",
            sample_sheet,
            RollContext(ability="str"),
        )
        assert result.details["roll_label"] == "Fuerza"
        assert result.details["modifier_breakdown"][0]["label"] == "Fuerza"
        assert "Fuerza" in result.chat_summary

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
        assert result.details["damage_type"] == "cortante"
        assert result.details["modifier_breakdown"]
        assert "1d8=6" in result.chat_summary
        assert result.chat_summary.endswith("= 9")


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
        assert attack.damage.is_healing is False

        updated, application = plugin.apply_damage(defender, attack.damage)
        assert application.hp_before == 16
        assert application.hp_after == 8
        assert updated["hp"]["current"] == 8

    def test_healing_roll_uses_curacion_label(self, plugin: Dnd5ePlugin, sample_sheet: dict, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 6 if b == 8 else 10)
        sheet = dict(sample_sheet)
        sheet["attacks"] = [
            {
                "name": "Curar heridas",
                "to_hit_bonus": 0,
                "damage_dice": "1d8+3",
                "damage_type": "radiante",
                "effect_type": "healing",
            }
        ]

        result = plugin.resolve_roll("healing", sheet, RollContext(attack_index=0))
        assert result.roll_type == "healing"
        assert result.details["is_healing"] is True
        assert result.details["effect_type"] == "healing"
        assert "Curación" in result.chat_summary
        assert "Daño" not in result.chat_summary

    def test_healing_attack_applies_capped_hp(self, plugin: Dnd5ePlugin, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 6 if b == 8 else 10)
        healer_sheet = {
            "attacks": [
                {
                    "name": "Curar heridas",
                    "to_hit_bonus": 0,
                    "damage_dice": "1d8+3",
                    "damage_type": "radiante",
                    "effect_type": "healing",
                }
            ]
        }
        defender = {"hp": {"max": 20, "current": 18, "temp": 0}, "ac": 10}

        attack = plugin.resolve_attack(
            healer_sheet,
            defender,
            "Curar heridas",
            AttackContext(),
        )
        assert attack.hit is True
        assert attack.damage is not None
        assert attack.damage.is_healing is True

        updated, application = plugin.apply_damage(defender, attack.damage)
        assert application.is_healing is True
        assert application.amount_applied == 2
        assert application.hp_before == 18
        assert application.hp_after == 20
        assert updated["hp"]["current"] == 20
        assert "Curación" in application.chat_summary

    def test_spell_save_dc_override(self, plugin: Dnd5ePlugin):
        sheet = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
        }
        validated = plugin.validate_pc_sheet(sheet)
        from app.rules.dnd5e.plugin import _spell_save_dc

        assert _spell_save_dc(validated) == 16

    def test_spell_save_dc_computed(self, plugin: Dnd5ePlugin):
        sheet = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": None},
        }
        validated = plugin.validate_pc_sheet(sheet)
        from app.rules.dnd5e.plugin import _spell_save_dc

        # 8 + 3 prof + 4 INT mod
        assert _spell_save_dc(validated) == 15

    def test_save_attack_fail_applies_full_damage(self, plugin: Dnd5ePlugin, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 5 if b == 20 else (6 if b == 8 else 4))

        caster = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "attacks": [
                {
                    "name": "Bola de fuego",
                    "damage_dice": "8d6",
                    "damage_type": "fuego",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "dex",
                    "half_damage_on_save": True,
                }
            ],
        }
        defender = {
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "proficiency_bonus": 2,
            "saving_throws": [],
        }

        attack = plugin.resolve_attack(caster, defender, "Bola de fuego", AttackContext())
        # DEX save: 5 + 0 = 5 vs CD 16 — fallo
        assert attack.attack_roll.details.get("save_succeeded") is False
        assert attack.hit is True
        assert attack.damage is not None
        assert attack.damage.amount == 32  # 8d6 con dados simulados (4 cada uno)
        assert attack.attack_roll.details.get("damage_roll_summary")

    def test_save_attack_fail_rolls_1d4(self, plugin: Dnd5ePlugin, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 5 if b == 20 else 3)

        caster = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "attacks": [
                {
                    "name": "Chispa",
                    "damage_dice": "1d4",
                    "damage_type": "fuego",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "dex",
                    "half_damage_on_save": False,
                }
            ],
        }
        defender = {
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "proficiency_bonus": 2,
            "saving_throws": [],
        }

        attack = plugin.resolve_attack(caster, defender, "Chispa", AttackContext())
        assert attack.attack_roll.details.get("save_succeeded") is False
        assert attack.damage is not None
        assert attack.damage.amount == 3
        assert attack.damage.expression == "1d4"

    def test_save_attack_success_half_damage(self, plugin: Dnd5ePlugin, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 18 if b == 20 else (6 if b == 8 else 4))

        caster = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "attacks": [
                {
                    "name": "Bola de fuego",
                    "damage_dice": "8d6",
                    "damage_type": "fuego",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "dex",
                    "half_damage_on_save": True,
                }
            ],
        }
        defender = {
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "proficiency_bonus": 2,
            "saving_throws": [],
        }

        attack = plugin.resolve_attack(caster, defender, "Bola de fuego", AttackContext())
        assert attack.attack_roll.details.get("save_succeeded") is True
        assert attack.damage is not None
        assert attack.damage.amount == 16  # mitad de 32

    def test_save_attack_success_no_damage(self, plugin: Dnd5ePlugin, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 18 if b == 20 else 4)

        caster = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "attacks": [
                {
                    "name": "Risa histérica de Tasha",
                    "damage_dice": "0",
                    "damage_type": "psíquico",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "wis",
                    "half_damage_on_save": False,
                }
            ],
        }
        defender = {
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "proficiency_bonus": 2,
            "saving_throws": [],
        }

        attack = plugin.resolve_attack(caster, defender, "Risa histérica de Tasha", AttackContext())
        assert attack.attack_roll.details.get("save_succeeded") is True
        assert attack.damage is None
        assert attack.hit is False
        assert "éxito" in attack.chat_summary

    def test_save_attack_fail_without_damage_dice(self, plugin: Dnd5ePlugin, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 5 if b == 20 else 4)

        caster = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "attacks": [
                {
                    "name": "Hechizo de control",
                    "damage_dice": "",
                    "damage_type": "psiquico",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "wis",
                    "half_damage_on_save": False,
                }
            ],
        }
        defender = {
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "proficiency_bonus": 2,
            "saving_throws": [],
        }

        attack = plugin.resolve_attack(caster, defender, "Hechizo de control", AttackContext())
        assert attack.attack_roll.details.get("save_succeeded") is False
        assert attack.damage is None
        assert attack.hit is True
        assert "fallo" in attack.chat_summary
        assert "damage_roll_summary" not in attack.attack_roll.details

    def test_save_attack_nested_empty_damage_dice(self, plugin: Dnd5ePlugin, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 18 if b == 20 else 4)

        caster = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "attacks": [
                {
                    "name": "Sugerencia",
                    "ability": "wis",
                    "resolution": "save",
                    "half_damage_on_save": False,
                    "effect_type": "damage",
                    "damage": {"dice": "", "type": "psiquico"},
                }
            ],
        }
        validated = plugin.validate_pc_sheet(caster)
        assert validated.attacks[0].damage_dice == ""

        attack = plugin.resolve_attack(caster, defender := {
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "proficiency_bonus": 2,
            "saving_throws": [],
        }, "Sugerencia", AttackContext())
        assert attack.attack_roll.details.get("save_succeeded") is True
        assert attack.damage is None

    def test_damage_consumes_temp_hp_first(self, plugin: Dnd5ePlugin):
        from app.rules.base import DamageResult

        defender = {"hp": {"max": 20, "current": 15, "temp": 5}, "ac": 10}
        updated, application = plugin.apply_damage(
            defender,
            DamageResult(
                amount=7,
                expression="7",
                rolls=[],
                damage_type="contundente",
            ),
        )
        assert updated["hp"]["temp"] == 0
        assert updated["hp"]["current"] == 13
        assert application.hp_after == 13

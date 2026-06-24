from app.rules.dnd5e.save_attack_format import (
    damage_type_label_es,
    format_save_attack_roll_line,
    format_save_damage_taken_line,
)


class TestSaveAttackFormat:
    def test_damage_type_label_es_known(self):
        assert damage_type_label_es("frio") == "frío"
        assert damage_type_label_es("psiquico") == "psíquico"

    def test_damage_type_label_es_omits_placeholder(self):
        assert damage_type_label_es("sin tipo") is None
        assert damage_type_label_es("untyped") is None
        assert damage_type_label_es("") is None

    def test_save_success_no_damage(self):
        line = format_save_attack_roll_line(
            defender_name="Esqueleto 2",
            ability_label="Sabiduría",
            total=15,
            save_dc=11,
            save_succeeded=True,
            attacker_name="Niolez",
            applies_damage=False,
        )
        assert "Esqueleto 2 supera" in line
        assert "el hechizo de Niolez no le afecta" in line

    def test_save_fail_full_effect(self):
        line = format_save_attack_roll_line(
            defender_name="Esqueleto 2",
            ability_label="Sabiduría",
            total=8,
            save_dc=11,
            save_succeeded=False,
            attacker_name="Niolez",
            applies_damage=True,
        )
        assert "Esqueleto 2 falla" in line
        assert "sufre el efecto completo" in line

    def test_save_success_half_damage(self):
        line = format_save_attack_roll_line(
            defender_name="Goblin",
            ability_label="Destreza",
            total=18,
            save_dc=16,
            save_succeeded=True,
            attacker_name="Mago",
            half_on_save=True,
            applies_damage=True,
        )
        assert "sufre la mitad del daño de Mago" in line

    def test_save_damage_taken_with_type(self):
        line = format_save_damage_taken_line(
            defender_name="Glavenus",
            amount=3,
            damage_type="frio",
        )
        assert line == "Glavenus pierde 3 PV de frío"

    def test_save_damage_taken_without_type(self):
        line = format_save_damage_taken_line(
            defender_name="Glavenus",
            amount=3,
            damage_type="untyped",
        )
        assert line == "Glavenus pierde 3 PV"

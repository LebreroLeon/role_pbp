import { Controller, useFieldArray, type Control, type UseFormRegister, type UseFormSetValue, type UseFormWatch } from "react-hook-form";

import { Button, Input, Switch } from "../../../../components/ui";
import {
  DND5E_ABILITIES,
  DND5E_ABILITY_LABELS,
  DND5E_SPELL_LEVEL_LABELS,
  abilityModifier,
  computedSpellAttackBonus,
  computedSpellSaveDc,
  type Dnd5eSheet,
} from "./schema";

type Dnd5eSpellcastingPanelProps = {
  control: Control<Dnd5eSheet>;
  register: UseFormRegister<Dnd5eSheet>;
  watch: UseFormWatch<Dnd5eSheet>;
  setValue: UseFormSetValue<Dnd5eSheet>;
  disabled?: boolean;
};

function formatMod(mod: number): string {
  return mod >= 0 ? `+${mod}` : String(mod);
}

export function Dnd5eSpellcastingPanel({
  control,
  register,
  watch,
  setValue,
  disabled,
}: Dnd5eSpellcastingPanelProps) {
  const abilities = watch("abilities");
  const proficiencyBonus = watch("proficiency.bonus") ?? 0;
  const spellcasting = watch("spellcasting");
  const spellAbility = spellcasting?.ability ?? "int";
  const saveDcOverride = spellcasting?.save_dc;
  const attackBonusOverride = spellcasting?.attack_bonus;
  const spells = spellcasting?.spells ?? [];
  const slots = spellcasting?.slots ?? [];

  const computedSaveDc = computedSpellSaveDc(spellAbility, proficiencyBonus, abilities ?? { str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10 });
  const computedAttack = computedSpellAttackBonus(spellAbility, proficiencyBonus, abilities ?? { str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10 });
  const displaySaveDc = saveDcOverride ?? computedSaveDc;
  const displayAttack = attackBonusOverride ?? computedAttack;

  const { fields, append, remove } = useFieldArray({ control, name: "spellcasting.spells" });

  function spellsForLevel(level: number) {
    return fields
      .map((field, index) => ({ field, index, spell: spells[index] }))
      .filter((entry) => (entry.spell?.level ?? 0) === level);
  }

  function addSpell(level: number) {
    append({ name: "", level, prepared: level > 0, ritual: false, notes: "" });
  }

  function resetSlotUsed(level: number) {
    const slotIndex = slots.findIndex((slot) => slot.level === level);
    if (slotIndex < 0) return;
    setValue(`spellcasting.slots.${slotIndex}.used`, 0, { shouldDirty: true });
  }

  return (
    <div className="sheet-spellcasting">
      <section className="sheet-section">
        <h3>Conjuración</h3>
        <div className="sheet-grid sheet-grid--2">
          <label className="form-field">
            <span>Atributo de conjuro</span>
            <select disabled={disabled} {...register("spellcasting.ability")}>
              {DND5E_ABILITIES.map((ability) => (
                <option key={ability} value={ability}>
                  {DND5E_ABILITY_LABELS[ability]} ({formatMod(abilityModifier(abilities?.[ability] ?? 10))})
                </option>
              ))}
            </select>
          </label>
          <div className="sheet-spellcasting__computed">
            <p className="muted sheet-spellcasting__hint">
              CD = 8 + competencia ({proficiencyBonus}) + mod. {DND5E_ABILITY_LABELS[spellAbility]} (
              {formatMod(abilityModifier(abilities?.[spellAbility] ?? 10))})
            </p>
            <div className="sheet-spellcasting__stats">
              <div className="sheet-spell-stat">
                <span>CD de conjuro</span>
                <strong>{displaySaveDc}</strong>
              </div>
              <div className="sheet-spell-stat">
                <span>Bonificador de ataque</span>
                <strong>{formatMod(displayAttack)}</strong>
              </div>
            </div>
          </div>
          <Input
            label="CD manual (opcional)"
            type="number"
            min={0}
            disabled={disabled}
            placeholder={String(computedSaveDc)}
            {...register("spellcasting.save_dc", {
              setValueAs: (value) => (value === "" || value === null ? null : Number(value)),
            })}
          />
          <Input
            label="Ataque manual (opcional)"
            type="number"
            disabled={disabled}
            placeholder={formatMod(computedAttack)}
            {...register("spellcasting.attack_bonus", {
              setValueAs: (value) => (value === "" || value === null ? null : Number(value)),
            })}
          />
        </div>
      </section>

      <section className="sheet-section">
        <h3>Espacios de conjuro</h3>
        <div className="sheet-spell-slots">
          {slots.map((slot, index) => (
            <div key={slot.level} className="sheet-spell-slot">
              <span className="sheet-spell-slot__label">{DND5E_SPELL_LEVEL_LABELS[slot.level]}</span>
              <Input
                label="Total"
                type="number"
                min={0}
                disabled={disabled}
                {...register(`spellcasting.slots.${index}.total`, { valueAsNumber: true })}
              />
              <Input
                label="Usados"
                type="number"
                min={0}
                disabled={disabled}
                {...register(`spellcasting.slots.${index}.used`, { valueAsNumber: true })}
              />
              <Button
                type="button"
                variant="secondary"
                disabled={disabled}
                onClick={() => resetSlotUsed(slot.level)}
              >
                Restaurar
              </Button>
            </div>
          ))}
        </div>
      </section>

      {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((level) => {
        const levelSpells = spellsForLevel(level);
        return (
          <section key={level} className="sheet-section">
            <div className="sheet-section__header">
              <h3>{DND5E_SPELL_LEVEL_LABELS[level]}</h3>
              <Button type="button" variant="secondary" disabled={disabled} onClick={() => addSpell(level)}>
                Añadir conjuro
              </Button>
            </div>
            {levelSpells.length === 0 ? (
              <p className="muted">Sin conjuros de {level === 0 ? "truco" : `nivel ${level}`}.</p>
            ) : (
              levelSpells.map(({ field, index }) => (
                <div key={field.id} className="sheet-spell-entry">
                  <Input
                    label="Nombre"
                    disabled={disabled}
                    {...register(`spellcasting.spells.${index}.name`)}
                  />
                  {level > 0 && (
                    <Controller
                      control={control}
                      name={`spellcasting.spells.${index}.prepared`}
                      render={({ field: preparedField }) => (
                        <Switch
                          className="sheet-switch sheet-switch--inline"
                          checked={preparedField.value}
                          onCheckedChange={preparedField.onChange}
                          disabled={disabled}
                          label="Preparado"
                          tone="teal"
                        />
                      )}
                    />
                  )}
                  <Controller
                    control={control}
                    name={`spellcasting.spells.${index}.ritual`}
                    render={({ field: ritualField }) => (
                      <Switch
                        className="sheet-switch sheet-switch--inline"
                        checked={ritualField.value}
                        onCheckedChange={ritualField.onChange}
                        disabled={disabled}
                        label="Ritual"
                        tone="rose"
                      />
                    )}
                  />
                  <label className="form-field">
                    <span>Notas</span>
                    <textarea disabled={disabled} rows={2} {...register(`spellcasting.spells.${index}.notes`)} />
                  </label>
                  <Button type="button" variant="secondary" disabled={disabled} onClick={() => remove(index)}>
                    Quitar
                  </Button>
                </div>
              ))
            )}
          </section>
        );
      })}
    </div>
  );
}

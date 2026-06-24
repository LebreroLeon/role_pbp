import { ChevronDown } from "lucide-react";
import { Controller, useFieldArray, type Control, type UseFormRegister, type UseFormSetValue, type UseFormWatch } from "react-hook-form";

import { Button } from "../../../../components/ui";
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

  const abilityScores = abilities ?? { str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10 };
  const computedSaveDc = computedSpellSaveDc(spellAbility, proficiencyBonus, abilityScores);
  const computedAttack = computedSpellAttackBonus(spellAbility, proficiencyBonus, abilityScores);
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
      <section className="sheet-section sheet-spellcasting__conjuration">
        <h3>Conjuración</h3>
        <p className="muted sheet-spellcasting__hint">
          CD = 8 + competencia ({proficiencyBonus}) + mod. {DND5E_ABILITY_LABELS[spellAbility]} (
          {formatMod(abilityModifier(abilityScores[spellAbility] ?? 10))})
        </p>
        <div className="sheet-spellcasting__stats-grid">
          <label className="form-field form-field--compact sheet-spellcasting__ability">
            <span>Atributo de conjuro</span>
            <select disabled={disabled} {...register("spellcasting.ability")}>
              {DND5E_ABILITIES.map((ability) => (
                <option key={ability} value={ability}>
                  {DND5E_ABILITY_LABELS[ability]} ({formatMod(abilityModifier(abilityScores[ability] ?? 10))})
                </option>
              ))}
            </select>
          </label>
          <div className="sheet-spell-stat sheet-spell-stat--compact">
            <span>CD de conjuro</span>
            <strong>{displaySaveDc}</strong>
          </div>
          <div className="sheet-spell-stat sheet-spell-stat--compact">
            <span>Bonif. ataque</span>
            <strong>{formatMod(displayAttack)}</strong>
          </div>
          <label className="form-field form-field--compact">
            <span>CD manual</span>
            <input
              type="number"
              min={0}
              disabled={disabled}
              placeholder={String(computedSaveDc)}
              {...register("spellcasting.save_dc", {
                setValueAs: (value) => (value === "" || value === null ? null : Number(value)),
              })}
            />
          </label>
          <label className="form-field form-field--compact">
            <span>Ataque manual</span>
            <input
              type="number"
              disabled={disabled}
              placeholder={formatMod(computedAttack)}
              {...register("spellcasting.attack_bonus", {
                setValueAs: (value) => (value === "" || value === null ? null : Number(value)),
              })}
            />
          </label>
        </div>
      </section>

      <section className="sheet-section">
        <h3>Espacios de conjuro</h3>
        <div className="sheet-spell-slots">
          {slots.map((slot, index) => (
            <div key={slot.level} className="sheet-spell-slot">
              <span className="sheet-spell-slot__label">{DND5E_SPELL_LEVEL_LABELS[slot.level]}</span>
              <label className="form-field form-field--compact">
                <span>Total</span>
                <input
                  type="number"
                  min={0}
                  disabled={disabled}
                  {...register(`spellcasting.slots.${index}.total`, { valueAsNumber: true })}
                />
              </label>
              <label className="form-field form-field--compact">
                <span>Usados</span>
                <input
                  type="number"
                  min={0}
                  disabled={disabled}
                  {...register(`spellcasting.slots.${index}.used`, { valueAsNumber: true })}
                />
              </label>
              <Button
                type="button"
                variant="secondary"
                className="sheet-spell-slot__reset"
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
          <section key={level} className="sheet-section sheet-spell-level">
            <div className="sheet-section__header">
              <h3>{DND5E_SPELL_LEVEL_LABELS[level]}</h3>
              <Button
                type="button"
                variant="secondary"
                className="sheet-spell-level__add"
                disabled={disabled}
                onClick={() => addSpell(level)}
              >
                Añadir
              </Button>
            </div>
            {levelSpells.length === 0 ? (
              <p className="muted sheet-spell-level__empty">
                Sin conjuros de {level === 0 ? "truco" : `nivel ${level}`}.
              </p>
            ) : (
              <div className="sheet-spell-list">
                {levelSpells.map(({ field, index, spell }) => (
                  <div key={field.id} className="sheet-spell-entry">
                    <div className="sheet-spell-entry__main">
                      <label className="sheet-spell-entry__name">
                        <span className="sr-only">Nombre del conjuro</span>
                        <input
                          type="text"
                          disabled={disabled}
                          placeholder="Nombre del conjuro"
                          {...register(`spellcasting.spells.${index}.name`)}
                        />
                      </label>
                      <div className="sheet-spell-entry__toggles">
                        {level > 0 && (
                          <Controller
                            control={control}
                            name={`spellcasting.spells.${index}.prepared`}
                            render={({ field: preparedField }) => (
                              <label className="sheet-spell-toggle">
                                <input
                                  type="checkbox"
                                  checked={preparedField.value}
                                  onChange={(event) => preparedField.onChange(event.target.checked)}
                                  disabled={disabled}
                                />
                                <span>Prep.</span>
                              </label>
                            )}
                          />
                        )}
                        <Controller
                          control={control}
                          name={`spellcasting.spells.${index}.ritual`}
                          render={({ field: ritualField }) => (
                            <label className="sheet-spell-toggle sheet-spell-toggle--ritual">
                              <input
                                type="checkbox"
                                checked={ritualField.value}
                                onChange={(event) => ritualField.onChange(event.target.checked)}
                                disabled={disabled}
                              />
                              <span>Ritual</span>
                            </label>
                          )}
                        />
                      </div>
                      <Button
                        type="button"
                        variant="secondary"
                        className="sheet-spell-entry__remove"
                        disabled={disabled}
                        onClick={() => remove(index)}
                      >
                        Quitar
                      </Button>
                    </div>
                    <details className="sheet-spell-entry__notes" {...(spell?.notes ? { open: true } : {})}>
                      <summary>
                        <span>Notas</span>
                        <ChevronDown size={14} aria-hidden />
                      </summary>
                      <textarea
                        disabled={disabled}
                        rows={2}
                        placeholder="Opcional"
                        {...register(`spellcasting.spells.${index}.notes`)}
                      />
                    </details>
                  </div>
                ))}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}

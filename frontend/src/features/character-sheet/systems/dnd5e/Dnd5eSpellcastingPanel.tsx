import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronDown, Send } from "lucide-react";
import { Controller, useFieldArray, type Control, type UseFormRegister, type UseFormSetValue, type UseFormWatch } from "react-hook-form";

import { api } from "../../../../api/client";
import { queryKeys } from "../../../../api/queryKeys";
import { Button, CollapsibleSection, Toast } from "../../../../components/ui";
import { useOpenSceneQuery } from "../../../../hooks/queries/useSceneQueries";
import type { SpeakerPayload } from "../../../scene/speakerOptions";
import { DND5E_DAMAGE_TYPE_GROUPS } from "./damageTypes";
import {
  DND5E_CASTING_TIME_OPTIONS,
  DND5E_SPELL_RESOLUTION_OPTIONS,
  DND5E_SPELL_SCHOOL_OPTIONS,
} from "./spellConstants";
import { formatSpellChatMessage } from "./spellChat";
import {
  DND5E_ABILITIES,
  DND5E_ABILITY_LABELS,
  DND5E_SPELL_LEVEL_LABELS,
  abilityModifier,
  computedSpellAttackBonus,
  computedSpellSaveDc,
  defaultSpellEntry,
  type Dnd5eSheet,
} from "./schema";

type Dnd5eSpellcastingPanelProps = {
  campaignId: string;
  control: Control<Dnd5eSheet>;
  register: UseFormRegister<Dnd5eSheet>;
  watch: UseFormWatch<Dnd5eSheet>;
  setValue: UseFormSetValue<Dnd5eSheet>;
  disabled?: boolean;
  spellPostSpeaker?: SpeakerPayload;
};

function formatMod(mod: number): string {
  return mod >= 0 ? `+${mod}` : String(mod);
}

export function Dnd5eSpellcastingPanel({
  campaignId,
  control,
  register,
  watch,
  setValue,
  disabled,
  spellPostSpeaker,
}: Dnd5eSpellcastingPanelProps) {
  const queryClient = useQueryClient();
  const { data: openScene } = useOpenSceneQuery(campaignId);
  const [postingSpellIndex, setPostingSpellIndex] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

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
    append(defaultSpellEntry(level));
  }

  function resetSlotUsed(level: number) {
    const slotIndex = slots.findIndex((slot) => slot.level === level);
    if (slotIndex < 0) return;
    setValue(`spellcasting.slots.${slotIndex}.used`, 0, { shouldDirty: true });
  }

  async function handlePostSpellToScene(spellIndex: number) {
    const spell = spells[spellIndex];
    if (!spell) return;

    if (!openScene) {
      setToastMessage("No hay escena abierta para publicar.");
      return;
    }
    if (openScene.status !== "ACTIVE" && openScene.status !== "PAUSED") {
      setToastMessage("La escena debe estar activa o pausada para publicar.");
      return;
    }

    const text = formatSpellChatMessage(spell);
    setPostingSpellIndex(spellIndex);
    try {
      const updated = await api.postMessage(openScene.id, text, "ACTION", spellPostSpeaker);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
      setToastMessage("Conjuro publicado en el chat de la escena.");
    } catch (err) {
      setToastMessage(err instanceof Error ? err.message : "No se pudo publicar el conjuro.");
    } finally {
      setPostingSpellIndex(null);
    }
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

      <section className="sheet-section sheet-spellcasting__list">
        <h3>Lista de conjuros</h3>
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((level) => {
          const levelSpells = spellsForLevel(level);
          const levelLabel = DND5E_SPELL_LEVEL_LABELS[level];
          const countLabel =
            levelSpells.length === 0
              ? "vacío"
              : levelSpells.length === 1
                ? "1 conjuro"
                : `${levelSpells.length} conjuros`;

          return (
            <CollapsibleSection
              key={level}
              title={levelLabel}
              description={countLabel}
              defaultOpen={levelSpells.length > 0}
              className="sheet-spell-level-collapsible"
            >
              <div className="sheet-spell-level__toolbar">
                <Button
                  type="button"
                  variant="secondary"
                  className="sheet-spell-level__add"
                  disabled={disabled}
                  onClick={() => addSpell(level)}
                >
                  Añadir conjuro
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
                          <Controller
                            control={control}
                            name={`spellcasting.spells.${index}.concentration`}
                            render={({ field: concentrationField }) => (
                              <label className="sheet-spell-toggle sheet-spell-toggle--concentration">
                                <input
                                  type="checkbox"
                                  checked={concentrationField.value}
                                  onChange={(event) => concentrationField.onChange(event.target.checked)}
                                  disabled={disabled}
                                />
                                <span>Conc.</span>
                              </label>
                            )}
                          />
                        </div>
                        <div className="sheet-spell-entry__actions">
                          <Button
                            type="button"
                            variant="secondary"
                            className="sheet-spell-entry__post"
                            disabled={disabled || postingSpellIndex === index}
                            onClick={() => handlePostSpellToScene(index)}
                          >
                            <Send size={14} aria-hidden />
                            {postingSpellIndex === index ? "Enviando…" : "Enviar a escena"}
                          </Button>
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
                      </div>

                      <div className="sheet-spell-entry__fields">
                        <label className="form-field form-field--compact">
                          <span>Tipo de lanzamiento</span>
                          <input
                            type="text"
                            list={`spell-casting-times-${index}`}
                            disabled={disabled}
                            placeholder="Acción"
                            {...register(`spellcasting.spells.${index}.casting_time`)}
                          />
                          <datalist id={`spell-casting-times-${index}`}>
                            {DND5E_CASTING_TIME_OPTIONS.map((option) => (
                              <option key={option} value={option} />
                            ))}
                          </datalist>
                        </label>
                        <label className="form-field form-field--compact">
                          <span>Escuela de magia</span>
                          <input
                            type="text"
                            list={`spell-schools-${index}`}
                            disabled={disabled}
                            placeholder="Evocación"
                            {...register(`spellcasting.spells.${index}.school`)}
                          />
                          <datalist id={`spell-schools-${index}`}>
                            {DND5E_SPELL_SCHOOL_OPTIONS.map((option) => (
                              <option key={option} value={option} />
                            ))}
                          </datalist>
                        </label>
                        <label className="form-field form-field--compact">
                          <span>Alcance</span>
                          <input
                            type="text"
                            disabled={disabled}
                            placeholder="18 m (60 pies)"
                            {...register(`spellcasting.spells.${index}.range`)}
                          />
                        </label>
                        <label className="form-field form-field--compact">
                          <span>Área de efecto</span>
                          <input
                            type="text"
                            disabled={disabled}
                            placeholder="Esfera de 6 m"
                            {...register(`spellcasting.spells.${index}.area`)}
                          />
                        </label>
                        <label className="form-field form-field--compact">
                          <span>Componentes</span>
                          <input
                            type="text"
                            disabled={disabled}
                            placeholder="V, S, M"
                            {...register(`spellcasting.spells.${index}.components`)}
                          />
                        </label>
                        <label className="form-field form-field--compact">
                          <span>Duración</span>
                          <input
                            type="text"
                            disabled={disabled}
                            placeholder="Instantánea"
                            {...register(`spellcasting.spells.${index}.duration`)}
                          />
                        </label>
                        <label className="form-field form-field--compact">
                          <span>Resolución</span>
                          <select disabled={disabled} {...register(`spellcasting.spells.${index}.resolution`)}>
                            {DND5E_SPELL_RESOLUTION_OPTIONS.map((option) => (
                              <option key={option || "none"} value={option}>
                                {option || "—"}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="form-field form-field--compact">
                          <span>Tipo de daño</span>
                          <select disabled={disabled} {...register(`spellcasting.spells.${index}.damage_type`)}>
                            <option value="">—</option>
                            {DND5E_DAMAGE_TYPE_GROUPS.map((group) => (
                              <optgroup key={group.label} label={group.label}>
                                {group.options.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </optgroup>
                            ))}
                          </select>
                        </label>
                      </div>

                      <label className="form-field sheet-spell-entry__description">
                        <span>Descripción</span>
                        <textarea
                          disabled={disabled}
                          rows={2}
                          placeholder="Efecto del conjuro"
                          {...register(`spellcasting.spells.${index}.notes`)}
                        />
                      </label>

                      <details
                        className="sheet-spell-entry__extra"
                        {...(spell?.higher_levels || spell?.end_conditions ? { open: true } : {})}
                      >
                        <summary>
                          <span>Escalado y finalización</span>
                          <ChevronDown size={14} aria-hidden />
                        </summary>
                        <div className="sheet-spell-entry__extra-fields">
                          <label className="form-field">
                            <span>Escalado a niveles superiores</span>
                            <textarea
                              disabled={disabled}
                              rows={2}
                              placeholder="Opcional"
                              {...register(`spellcasting.spells.${index}.higher_levels`)}
                            />
                          </label>
                          <label className="form-field">
                            <span>Condiciones de finalización</span>
                            <textarea
                              disabled={disabled}
                              rows={2}
                              placeholder="Opcional"
                              {...register(`spellcasting.spells.${index}.end_conditions`)}
                            />
                          </label>
                        </div>
                      </details>
                    </div>
                  ))}
                </div>
              )}
            </CollapsibleSection>
          );
        })}
      </section>

      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
    </div>
  );
}

import { useState } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, ClipboardList, Dices, Sparkles } from "lucide-react";

import type { SheetRollRequest, SheetRollResponse } from "../../../../api/types";
import { Button, CollapsibleSection, Input, Switch, Tooltip } from "../../../../components/ui";
import { mergeAdvantageIntoContext, type AdvantageMode } from "../../../systems";
import { AdvantageToggle } from "../../../systems/dnd5e/AdvantageToggle";
import { dnd5eSkillModifier } from "../../../systems/dnd5e/rolls";
import { passivePerception } from "./mechanics";
import {
  DND5E_ABILITIES,
  DND5E_ABILITY_LABELS,
  DND5E_SKILL_GROUPS,
  abilityModifier,
  dnd5eSheetSchema,
  skillLabelEs,
  type Dnd5eAbility,
  type Dnd5eSheet,
} from "./schema";
import { DND5E_DAMAGE_TYPE_GROUPS, DND5E_DAMAGE_TYPE_VALUES, damageTypeLabel } from "./damageTypes";
import type { Dnd5eDamageType } from "./damageTypes";
import { InspirationBox, InspirationSpendToggle } from "./InspirationBox";
import { Dnd5eSpellcastingPanel } from "./Dnd5eSpellcastingPanel";

type Dnd5eSheetFormProps = {
  defaultValues: Dnd5eSheet;
  onSubmit: (sheet: Dnd5eSheet) => void;
  onRoll?: (payload: SheetRollRequest) => Promise<SheetRollResponse | void> | SheetRollResponse | void;
  disabled?: boolean;
  isSaving?: boolean;
  isRolling?: boolean;
  /** Master-only: grant or revoke inspiration on this sheet. */
  canGrantInspiration?: boolean;
};

type RollButtonProps = {
  label: string;
  disabled?: boolean;
  onClick: () => void;
};

function RollButton({ label, disabled, onClick }: RollButtonProps) {
  return (
    <Tooltip content={label}>
      <Button
        type="button"
        variant="secondary"
        className="sheet-roll-btn"
        disabled={disabled}
        onClick={onClick}
        aria-label={label}
      >
        <Dices size={14} strokeWidth={2} />
      </Button>
    </Tooltip>
  );
}

type DeathSaveDotsProps = {
  label: string;
  count: number;
  variant: "success" | "failure";
  disabled?: boolean;
  onChange: (value: number) => void;
};

function DeathSaveDots({ label, count, variant, disabled, onChange }: DeathSaveDotsProps) {
  return (
    <div className="sheet-death-saves__row">
      <span className="sheet-death-saves__label">{label}</span>
      <div className="sheet-death-saves__dots" role="group" aria-label={label}>
        {[0, 1, 2].map((index) => {
          const filled = index < count;
          return (
            <button
              key={index}
              type="button"
              className={`sheet-death-dot sheet-death-dot--${variant}${filled ? " is-filled" : ""}`}
              disabled={disabled}
              aria-pressed={filled}
              aria-label={`${label} ${index + 1}`}
              onClick={() => onChange(filled && count === index + 1 ? index : index + 1)}
            />
          );
        })}
      </div>
    </div>
  );
}

function formatMod(mod: number): string {
  return mod >= 0 ? `+${mod}` : String(mod);
}

type DamageModifierField = "resistances" | "vulnerabilities" | "immunities";

function toggleDamageModifierList(
  selected: Dnd5eDamageType[],
  value: Dnd5eDamageType,
  enabled: boolean,
): Dnd5eDamageType[] {
  if (enabled) {
    return selected.includes(value) ? selected : [...selected, value];
  }
  return selected.filter((item) => item !== value);
}

function formatDamageDefenseSummary(resistances: number, vulnerabilities: number, immunities: number): string {
  return `${resistances} res · ${vulnerabilities} vul · ${immunities} inm`;
}

export function Dnd5eSheetForm({
  defaultValues,
  onSubmit,
  onRoll,
  disabled,
  isSaving,
  isRolling,
  canGrantInspiration = false,
}: Dnd5eSheetFormProps) {
  const rollDisabled = disabled || isRolling || !onRoll;
  const [advantageMode, setAdvantageMode] = useState<AdvantageMode>("normal");
  const [spendInspiration, setSpendInspiration] = useState(false);

  async function rollWithAdvantage(payload: SheetRollRequest) {
    const mode = spendInspiration ? "advantage" : advantageMode;
    const result = await onRoll?.({
      ...payload,
      context: mergeAdvantageIntoContext(payload.context, mode),
    });

    if (spendInspiration && result) {
      setValue("roleplay.inspiration", false, { shouldDirty: true });
      setSpendInspiration(false);
      onSubmit(getValues());
    }

    return result;
  }

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<Dnd5eSheet>({
    resolver: zodResolver(dnd5eSheetSchema),
    defaultValues,
  });

  const { fields, append, remove } = useFieldArray({ control, name: "attacks" });
  const abilities = watch("abilities");
  const skills = watch("proficiency.skills");
  const attacks = watch("attacks");
  const savingThrows = watch("proficiency.saving_throws") ?? [];
  const proficiencyBonus = watch("proficiency.bonus") ?? 0;
  const deathSuccesses = watch("defense.death_saves.successes") ?? 0;
  const deathFailures = watch("defense.death_saves.failures") ?? 0;
  const resistances = watch("defense.damage_modifiers.resistances") ?? [];
  const vulnerabilities = watch("defense.damage_modifiers.vulnerabilities") ?? [];
  const immunities = watch("defense.damage_modifiers.immunities") ?? [];
  const hasInspiration = watch("roleplay.inspiration") ?? false;

  const perceptionSkill = skills?.find(
    (skill) => skill.name.trim().toLowerCase().replace(/\s+/g, "_") === "perception",
  );
  const passiveWisdom = passivePerception(
    abilities?.wis ?? 10,
    proficiencyBonus,
    perceptionSkill?.proficient ?? false,
    perceptionSkill?.expertise ?? false,
  );

  function toggleSavingThrow(ability: Dnd5eAbility, enabled: boolean) {
    if (enabled) {
      if (!savingThrows.includes(ability)) {
        setValue("proficiency.saving_throws", [...savingThrows, ability], { shouldDirty: true });
      }
      return;
    }

    setValue(
      "proficiency.saving_throws",
      savingThrows.filter((entry) => entry !== ability),
      { shouldDirty: true },
    );
  }

  function savingThrowMod(ability: Dnd5eAbility): number {
    const mod = abilityModifier(abilities?.[ability] ?? 10);
    return savingThrows.includes(ability) ? mod + proficiencyBonus : mod;
  }

  function skillIndex(skillName: string): number {
    return skills?.findIndex((skill) => skill.name === skillName) ?? -1;
  }

  function skillMod(skillName: string): number {
    return dnd5eSkillModifier(
      {
        abilities: abilities ?? defaultValues.abilities,
        proficiency: {
          bonus: proficiencyBonus,
          skills: skills ?? [],
        },
      },
      skillName,
      abilityModifier,
    );
  }

  function rollAbilityCheck(ability: Dnd5eAbility) {
    rollWithAdvantage({ roll_type: "ability_check", context: { ability } });
  }

  function rollSavingThrow(ability: Dnd5eAbility) {
    rollWithAdvantage({ roll_type: "saving_throw", context: { ability } });
  }

  function rollSkillCheck(skillName: string) {
    rollWithAdvantage({ roll_type: "skill_check", context: { skill: skillName } });
  }

  function rollDamage(index: number) {
    const attack = attacks?.[index];
    const isHealing = attack?.effect_type === "healing";
    onRoll?.({
      roll_type: isHealing ? "healing" : "damage",
      context: {
        attack_index: index,
        ...(attack?.name ? { attack_name: attack.name } : {}),
      },
    });
  }

  function rollInitiative() {
    rollWithAdvantage({ roll_type: "initiative" });
  }

  function setDamageModifier(field: DamageModifierField, value: Dnd5eDamageType, enabled: boolean) {
    const selected =
      field === "resistances" ? resistances : field === "vulnerabilities" ? vulnerabilities : immunities;
    setValue(
      `defense.damage_modifiers.${field}`,
      toggleDamageModifierList(selected, value, enabled),
      { shouldDirty: true },
    );
  }

  function toggleSpendInspiration(active: boolean) {
    setSpendInspiration(active);
    if (active) {
      setAdvantageMode("advantage");
    }
  }

  function toggleInspiration(active: boolean) {
    setValue("roleplay.inspiration", active, { shouldDirty: true });
    if (!active) {
      setSpendInspiration(false);
    }
  }

  function rollAttack(index: number) {
    const attack = attacks?.[index];
    rollWithAdvantage({
      roll_type: "attack_roll",
      context: {
        attack_index: index,
        ...(attack?.name ? { attack_name: attack.name } : {}),
      },
    });
  }

  async function rollDeathSave() {
    const result = await onRoll?.({ roll_type: "death_save", context: {} });
    const details = result?.roll_details;
    if (!details) return;

    if (typeof details.death_save_successes === "number") {
      setValue("defense.death_saves.successes", details.death_save_successes, { shouldDirty: true });
    }
    if (typeof details.death_save_failures === "number") {
      setValue("defense.death_saves.failures", details.death_save_failures, { shouldDirty: true });
    }
    if (typeof details.hp_current === "number") {
      setValue("defense.hp.current", details.hp_current, { shouldDirty: true });
    }

    const updated = getValues();
    onSubmit(updated);
  }

  return (
    <form className="sheet-form" onSubmit={handleSubmit(onSubmit)}>
      <CollapsibleSection
        icon={ClipboardList}
        iconTone="teal"
        title="Ficha mecánica"
        description="Atributos, defensa, habilidades, equipo y ataques."
        defaultOpen
        className="sheet-mechanics-collapsible"
      >
      <div className="sheet-form__roll-toolbar">
        <AdvantageToggle value={advantageMode} onChange={setAdvantageMode} disabled={rollDisabled} />
        {hasInspiration && (
          <InspirationSpendToggle
            active={spendInspiration}
            disabled={rollDisabled}
            onToggle={toggleSpendInspiration}
          />
        )}
      </div>

      <div className="sheet-header-stats">
        <div className="sheet-header-stats__inspiration">
          <InspirationBox
            active={hasInspiration}
            disabled={disabled}
            readOnly={!canGrantInspiration}
            onToggle={toggleInspiration}
          />
        </div>
        <div className="sheet-passive-perception" aria-label="Percepción pasiva">
          <span className="sheet-passive-perception__label">Percepción pasiva (Sab)</span>
          <strong className="sheet-passive-perception__value">{passiveWisdom}</strong>
        </div>
      </div>

      <section className="sheet-section">
        <h3>Identidad</h3>
        <div className="sheet-grid sheet-grid--2">
          <Input label="Clase" disabled={disabled} {...register("identity.class")} />
          <Input
            label="Nivel"
            type="number"
            min={1}
            max={20}
            disabled={disabled}
            error={errors.identity?.level?.message}
            {...register("identity.level", { valueAsNumber: true })}
          />
          <Input label="Trasfondo" disabled={disabled} {...register("identity.background")} />
          <Input label="Raza" disabled={disabled} {...register("identity.race")} />
          <Input label="Alineación" disabled={disabled} {...register("identity.alignment")} />
        </div>
      </section>

      <section className="sheet-section">
        <h3>Atributos</h3>
        <div className="sheet-abilities">
          {DND5E_ABILITIES.map((ability) => {
            const score = abilities?.[ability] ?? 10;
            const mod = abilityModifier(Number(score));
            return (
              <div key={ability} className="sheet-ability">
                <label className="form-field">
                  <span>{DND5E_ABILITY_LABELS[ability]}</span>
                  <input
                    type="number"
                    min={1}
                    max={30}
                    disabled={disabled}
                    {...register(`abilities.${ability}`, { valueAsNumber: true })}
                  />
                </label>
                <div className="sheet-ability__footer">
                  <span className="sheet-ability__mod" aria-label={`Modificador de ${DND5E_ABILITY_LABELS[ability]}`}>
                    {formatMod(mod)}
                  </span>
                  <RollButton
                    label={`Tirar ${DND5E_ABILITY_LABELS[ability]}`}
                    disabled={rollDisabled}
                    onClick={() => rollAbilityCheck(ability)}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="sheet-section">
        <h3>Defensa</h3>
        <div className="sheet-grid sheet-grid--3">
          <Input
            label="Clase de armadura (CA)"
            type="number"
            min={0}
            disabled={disabled}
            error={errors.defense?.ac?.message}
            {...register("defense.ac", { valueAsNumber: true })}
          />
          <Input
            label="PV máximos"
            type="number"
            min={1}
            disabled={disabled}
            error={errors.defense?.hp?.max?.message}
            {...register("defense.hp.max", { valueAsNumber: true })}
          />
          <Input
            label="PV actuales"
            type="number"
            min={0}
            disabled={disabled}
            error={errors.defense?.hp?.current?.message}
            {...register("defense.hp.current", { valueAsNumber: true })}
          />
          <Input
            label="PV temporales"
            type="number"
            min={0}
            disabled={disabled}
            {...register("defense.hp.temp", { valueAsNumber: true })}
          />
          <Input label="Dados de golpe" disabled={disabled} {...register("defense.hit_dice")} />
          <Input
            label="Bonificador de competencia"
            type="number"
            min={0}
            disabled={disabled}
            {...register("proficiency.bonus", { valueAsNumber: true })}
          />
          <Input
            label="Velocidad"
            placeholder="9 m (30 pies)"
            disabled={disabled}
            {...register("defense.speed")}
          />
        </div>

        <div className="sheet-death-saves">
          <div className="sheet-death-saves__header">
            <h4>Salvaciones contra la muerte</h4>
            <Button type="button" variant="secondary" disabled={rollDisabled} onClick={rollDeathSave}>
              Tirar salvación
            </Button>
          </div>
          <DeathSaveDots
            label="Éxitos"
            count={deathSuccesses}
            variant="success"
            disabled={disabled}
            onChange={(value) =>
              setValue("defense.death_saves.successes", value, { shouldDirty: true })
            }
          />
          <DeathSaveDots
            label="Fallos"
            count={deathFailures}
            variant="failure"
            disabled={disabled}
            onChange={(value) =>
              setValue("defense.death_saves.failures", value, { shouldDirty: true })
            }
          />
        </div>

        <details className="sheet-damage-defenses">
          <summary className="sheet-damage-defenses__summary">
            <h4>Defensas de daño</h4>
            <span className="sheet-damage-defenses__summary-end">
              <span className="sheet-damage-defenses__counts">
                {formatDamageDefenseSummary(resistances.length, vulnerabilities.length, immunities.length)}
              </span>
              <ChevronDown className="sheet-damage-defenses__chevron" size={18} aria-hidden />
            </span>
          </summary>
          <div className="sheet-damage-defenses__grid" role="group" aria-label="Defensas de daño">
            {DND5E_DAMAGE_TYPE_VALUES.map((damageType) => (
              <div key={damageType} className="sheet-damage-defense-row">
                <span className="sheet-damage-defense-row__name">{damageTypeLabel(damageType)}</span>
                <Switch
                  id={`damage-${damageType}-res`}
                  className="sheet-switch sheet-switch--compact"
                  checked={resistances.includes(damageType)}
                  onCheckedChange={(enabled) => setDamageModifier("resistances", damageType, enabled)}
                  disabled={disabled}
                  label="Res"
                  tone="teal"
                />
                <Switch
                  id={`damage-${damageType}-vul`}
                  className="sheet-switch sheet-switch--compact"
                  checked={vulnerabilities.includes(damageType)}
                  onCheckedChange={(enabled) => setDamageModifier("vulnerabilities", damageType, enabled)}
                  disabled={disabled}
                  label="Vul"
                  tone="rose"
                />
                <Switch
                  id={`damage-${damageType}-inm`}
                  className="sheet-switch sheet-switch--compact"
                  checked={immunities.includes(damageType)}
                  onCheckedChange={(enabled) => setDamageModifier("immunities", damageType, enabled)}
                  disabled={disabled}
                  label="Inm"
                  tone="teal"
                />
              </div>
            ))}
          </div>
        </details>
      </section>

      <section className="sheet-section">
        <div className="sheet-section__header">
          <h3>Iniciativa</h3>
          <RollButton label="Tirar iniciativa" disabled={rollDisabled} onClick={rollInitiative} />
        </div>
        <Input
          label="Modificador adicional"
          type="number"
          disabled={disabled}
          {...register("initiative.modifier", { valueAsNumber: true })}
        />
      </section>

      <section className="sheet-section">
        <h3>Tiradas de salvación y habilidades</h3>
        <div className="sheet-ability-groups">
          {DND5E_SKILL_GROUPS.map((group) => (
            <div key={group.ability} className="sheet-ability-group">
              <div className="sheet-ability-group__header">
                <span className="sheet-ability-group__title">{DND5E_ABILITY_LABELS[group.ability]}</span>
                <span className="sheet-ability-group__mod">{formatMod(abilityModifier(abilities?.[group.ability] ?? 10))}</span>
              </div>

              <div className="sheet-saving-throw-row">
                <Switch
                  className="sheet-switch sheet-switch--compact"
                  checked={savingThrows.includes(group.ability)}
                  onCheckedChange={(enabled) => toggleSavingThrow(group.ability, enabled)}
                  disabled={disabled}
                  label="Salvación"
                  tone="teal"
                />
                <span className="sheet-mod-badge">{formatMod(savingThrowMod(group.ability))}</span>
                <RollButton
                  label={`Tirar salvación de ${DND5E_ABILITY_LABELS[group.ability]}`}
                  disabled={rollDisabled}
                  onClick={() => rollSavingThrow(group.ability)}
                />
              </div>

              {group.skills.map((skillName) => {
                const index = skillIndex(skillName);
                if (index < 0) return null;
                return (
                  <div key={skillName} className="sheet-skill-row">
                    <span className="sheet-skill-row__name">{skillLabelEs(skillName)}</span>
                    <Controller
                      control={control}
                      name={`proficiency.skills.${index}.proficient`}
                      render={({ field }) => (
                        <Switch
                          className="sheet-switch sheet-switch--compact"
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          disabled={disabled}
                          label="Comp."
                          tone="teal"
                        />
                      )}
                    />
                    <Controller
                      control={control}
                      name={`proficiency.skills.${index}.expertise`}
                      render={({ field }) => (
                        <Switch
                          className="sheet-switch sheet-switch--compact"
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          disabled={disabled}
                          label="Exp."
                          tone="rose"
                        />
                      )}
                    />
                    <span className="sheet-mod-badge">{formatMod(skillMod(skillName))}</span>
                    <RollButton
                      label={`Tirar ${skillLabelEs(skillName)}`}
                      disabled={rollDisabled}
                      onClick={() => rollSkillCheck(skillName)}
                    />
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </section>

      <section className="sheet-section">
        <h3>Rol</h3>
        <div className="sheet-textareas">
          <label className="form-field">
            <span>Rasgos de personalidad</span>
            <textarea disabled={disabled} rows={3} {...register("roleplay.personality_traits")} />
          </label>
          <label className="form-field">
            <span>Ideales</span>
            <textarea disabled={disabled} rows={2} {...register("roleplay.ideals")} />
          </label>
          <label className="form-field">
            <span>Vínculos</span>
            <textarea disabled={disabled} rows={2} {...register("roleplay.bonds")} />
          </label>
          <label className="form-field">
            <span>Defectos</span>
            <textarea disabled={disabled} rows={2} {...register("roleplay.flaws")} />
          </label>
        </div>
      </section>

      <section className="sheet-section">
        <h3>Rasgos y atributos</h3>
        <label className="form-field">
          <span>Características, dotes y rasgos de especie/clase</span>
          <textarea disabled={disabled} rows={5} {...register("features_traits")} />
        </label>
      </section>

      <section className="sheet-section">
        <h3>Otras competencias</h3>
        <label className="form-field">
          <span>Idiomas, herramientas, competencias adicionales</span>
          <textarea disabled={disabled} rows={4} {...register("other_proficiencies")} />
        </label>
      </section>

      <section className="sheet-section">
        <h3>Equipo</h3>
        <label className="form-field">
          <span>Objetos y equipo</span>
          <textarea disabled={disabled} rows={5} {...register("equipment")} />
        </label>
        <div className="sheet-currency">
          <Input label="CP" type="number" min={0} disabled={disabled} {...register("currency.cp", { valueAsNumber: true })} />
          <Input label="SP" type="number" min={0} disabled={disabled} {...register("currency.sp", { valueAsNumber: true })} />
          <Input label="EP" type="number" min={0} disabled={disabled} {...register("currency.ep", { valueAsNumber: true })} />
          <Input label="GP" type="number" min={0} disabled={disabled} {...register("currency.gp", { valueAsNumber: true })} />
          <Input label="PP" type="number" min={0} disabled={disabled} {...register("currency.pp", { valueAsNumber: true })} />
        </div>
      </section>

      <section className="sheet-section">
        <div className="sheet-section__header">
          <h3>Ataques</h3>
          <Button
            type="button"
            variant="secondary"
            disabled={disabled}
            onClick={() =>
              append({
                name: "",
                ability: "str",
                proficient: false,
                resolution: "attack_roll",
                half_damage_on_save: false,
                effect_type: "damage",
                damage: { dice: "1d8", type: "contundente" },
                properties: [],
              })
            }
          >
            Añadir ataque
          </Button>
        </div>
        {fields.map((field, index) => (
          <div key={field.id} className="sheet-attack">
            <Input
              label="Nombre"
              disabled={disabled}
              error={errors.attacks?.[index]?.name?.message}
              {...register(`attacks.${index}.name`)}
            />
            <label className="form-field">
              <span>Resolución</span>
              <select disabled={disabled} {...register(`attacks.${index}.resolution`)}>
                <option value="attack_roll">Tirada de ataque (vs CA)</option>
                <option value="save">Salvación (vs CD)</option>
              </select>
            </label>
            <label className="form-field">
              <span>
                {attacks?.[index]?.resolution === "save"
                  ? "Atributo de salvación"
                  : "Atributo de ataque"}
              </span>
              <select disabled={disabled} {...register(`attacks.${index}.ability`)}>
                {DND5E_ABILITIES.map((ability) => (
                  <option key={ability} value={ability}>
                    {DND5E_ABILITY_LABELS[ability]}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label={attacks?.[index]?.effect_type === "healing" ? "Curación (dados)" : "Daño (dados)"}
              disabled={disabled}
              error={errors.attacks?.[index]?.damage?.dice?.message}
              {...register(`attacks.${index}.damage.dice`)}
            />
            <label className="form-field">
              <span>Efecto</span>
              <select disabled={disabled} {...register(`attacks.${index}.effect_type`)}>
                <option value="damage">Daño</option>
                <option value="healing">Curación</option>
              </select>
            </label>
            <label className="form-field">
              <span>Tipo de daño</span>
              <select disabled={disabled} {...register(`attacks.${index}.damage.type`)}>
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
              {errors.attacks?.[index]?.damage?.type?.message ? (
                <span className="form-field__error">{errors.attacks[index]?.damage?.type?.message}</span>
              ) : null}
            </label>
            {attacks?.[index]?.resolution !== "save" ? (
              <Controller
                control={control}
                name={`attacks.${index}.proficient`}
                render={({ field }) => (
                  <Switch
                    className="sheet-switch sheet-switch--inline"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    disabled={disabled}
                    label="Competente"
                    tone="teal"
                  />
                )}
              />
            ) : null}
            {attacks?.[index]?.resolution === "save" && attacks?.[index]?.effect_type === "damage" ? (
              <Controller
                control={control}
                name={`attacks.${index}.half_damage_on_save`}
                render={({ field }) => (
                  <Switch
                    className="sheet-switch sheet-switch--inline"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    disabled={disabled}
                    label="Mitad de daño si salva"
                    tone="teal"
                  />
                )}
              />
            ) : null}
            <div className="sheet-attack__rolls">
              {attacks?.[index]?.resolution !== "save" && (
                <Button type="button" variant="secondary" disabled={rollDisabled} onClick={() => rollAttack(index)}>
                  Tirar ataque
                </Button>
              )}
              <Button type="button" variant="secondary" disabled={rollDisabled} onClick={() => rollDamage(index)}>
                {attacks?.[index]?.effect_type === "healing" ? "Tirar curación" : "Tirar daño"}
              </Button>
            </div>
            {fields.length > 1 && (
              <Button type="button" variant="secondary" disabled={disabled} onClick={() => remove(index)}>
                Quitar
              </Button>
            )}
          </div>
        ))}
      </section>
      </CollapsibleSection>

      <CollapsibleSection
        icon={Sparkles}
        iconTone="violet"
        title="Conjuros"
        description="CD, espacios de conjuro y lista de hechizos."
        className="sheet-spellcasting-collapsible"
      >
        <Dnd5eSpellcastingPanel
          control={control}
          register={register}
          watch={watch}
          setValue={setValue}
          disabled={disabled}
        />
      </CollapsibleSection>

      <div className="actions">
        <Button type="submit" disabled={disabled || isSaving}>
          {isSaving ? "Guardando..." : "Guardar ficha"}
        </Button>
      </div>
    </form>
  );
}

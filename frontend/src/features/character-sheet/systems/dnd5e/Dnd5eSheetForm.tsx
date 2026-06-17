import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Dices } from "lucide-react";

import type { SheetRollRequest } from "../../../../api/types";
import { Button, Input } from "../../../../components/ui";
import {
  DND5E_ABILITIES,
  DND5E_ABILITY_LABELS,
  abilityModifier,
  dnd5eSheetSchema,
  type Dnd5eAbility,
  type Dnd5eSheet,
} from "./schema";

type Dnd5eSheetFormProps = {
  defaultValues: Dnd5eSheet;
  onSubmit: (sheet: Dnd5eSheet) => void;
  onRoll?: (payload: SheetRollRequest) => void;
  disabled?: boolean;
  isSaving?: boolean;
  isRolling?: boolean;
};

type RollButtonProps = {
  label: string;
  disabled?: boolean;
  onClick: () => void;
};

function RollButton({ label, disabled, onClick }: RollButtonProps) {
  return (
    <Button
      type="button"
      variant="secondary"
      className="sheet-roll-btn"
      disabled={disabled}
      onClick={onClick}
      aria-label={label}
      title={label}
    >
      <Dices size={14} strokeWidth={2} />
    </Button>
  );
}

export function Dnd5eSheetForm({
  defaultValues,
  onSubmit,
  onRoll,
  disabled,
  isSaving,
  isRolling,
}: Dnd5eSheetFormProps) {
  const rollDisabled = disabled || isRolling || !onRoll;

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<Dnd5eSheet>({
    resolver: zodResolver(dnd5eSheetSchema),
    defaultValues,
  });

  const { fields, append, remove } = useFieldArray({ control, name: "attacks" });
  const abilities = watch("abilities");
  const skills = watch("proficiency.skills");
  const attacks = watch("attacks");

  function rollAbilityCheck(ability: Dnd5eAbility) {
    onRoll?.({ roll_type: "ability_check", context: { ability } });
  }

  function rollSavingThrow(ability: Dnd5eAbility) {
    onRoll?.({ roll_type: "saving_throw", context: { ability } });
  }

  function rollSkillCheck(skillName: string) {
    onRoll?.({ roll_type: "skill_check", context: { skill: skillName } });
  }

  function rollDamage(index: number) {
    const attack = attacks?.[index];
    onRoll?.({
      roll_type: "damage",
      context: {
        attack_index: index,
        ...(attack?.name ? { attack_name: attack.name } : {}),
      },
    });
  }

  function rollInitiative() {
    onRoll?.({ roll_type: "initiative" });
  }

  return (
    <form className="sheet-form" onSubmit={handleSubmit(onSubmit)}>
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
                    {mod >= 0 ? `+${mod}` : mod}
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
        </div>
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
        <h3>Tiradas de salvación</h3>
        <div className="sheet-saving-throws">
          {DND5E_ABILITIES.map((ability) => (
            <div key={ability} className="sheet-saving-throw">
              <label className="sheet-checkbox">
                <input type="checkbox" disabled={disabled} value={ability} {...register("proficiency.saving_throws")} />
                {DND5E_ABILITY_LABELS[ability]}
              </label>
              <RollButton
                label={`Tirar salvación de ${DND5E_ABILITY_LABELS[ability]}`}
                disabled={rollDisabled}
                onClick={() => rollSavingThrow(ability)}
              />
            </div>
          ))}
        </div>
      </section>

      <section className="sheet-section">
        <h3>Habilidades</h3>
        <div className="sheet-skills">
          {skills?.map((skill, index) => (
            <div key={skill.name} className="sheet-skill">
              <span className="sheet-skill__name">{skill.name}</span>
              <label className="sheet-checkbox">
                <input type="checkbox" disabled={disabled} {...register(`proficiency.skills.${index}.proficient`)} />
                Competente
              </label>
              <label className="sheet-checkbox">
                <input type="checkbox" disabled={disabled} {...register(`proficiency.skills.${index}.expertise`)} />
                Experto
              </label>
              <RollButton
                label={`Tirar ${skill.name}`}
                disabled={rollDisabled}
                onClick={() => rollSkillCheck(skill.name)}
              />
            </div>
          ))}
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
              <span>Atributo</span>
              <select disabled={disabled} {...register(`attacks.${index}.ability`)}>
                {DND5E_ABILITIES.map((ability) => (
                  <option key={ability} value={ability}>
                    {DND5E_ABILITY_LABELS[ability]}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label="Daño (dados)"
              disabled={disabled}
              error={errors.attacks?.[index]?.damage?.dice?.message}
              {...register(`attacks.${index}.damage.dice`)}
            />
            <Input
              label="Tipo de daño"
              disabled={disabled}
              error={errors.attacks?.[index]?.damage?.type?.message}
              {...register(`attacks.${index}.damage.type`)}
            />
            <label className="sheet-checkbox">
              <input type="checkbox" disabled={disabled} {...register(`attacks.${index}.proficient`)} />
              Competente
            </label>
            <div className="sheet-attack__rolls">
              <Button type="button" variant="secondary" disabled={rollDisabled} onClick={() => rollDamage(index)}>
                Tirar daño
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

      <div className="actions">
        <Button type="submit" disabled={disabled || isSaving}>
          {isSaving ? "Guardando..." : "Guardar ficha"}
        </Button>
      </div>
    </form>
  );
}

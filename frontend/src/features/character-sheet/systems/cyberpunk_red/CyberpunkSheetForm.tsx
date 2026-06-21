import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Dices } from "lucide-react";

import type { SheetRollRequest } from "../../../../api/types";
import { Button, Input, Tooltip } from "../../../../components/ui";
import {
  CYBERPUNK_STATS,
  CYBERPUNK_STAT_LABELS,
  cyberpunkRedSheetSchema,
  type CyberpunkRedSheet,
  type CyberpunkStat,
} from "./schema";

type CyberpunkSheetFormProps = {
  defaultValues: CyberpunkRedSheet;
  onSubmit: (sheet: CyberpunkRedSheet) => void;
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

export function CyberpunkSheetForm({
  defaultValues,
  onSubmit,
  onRoll,
  disabled,
  isSaving,
  isRolling,
}: CyberpunkSheetFormProps) {
  const rollDisabled = disabled || isRolling || !onRoll;

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<CyberpunkRedSheet>({
    resolver: zodResolver(cyberpunkRedSheetSchema),
    defaultValues,
  });

  const { fields, append, remove } = useFieldArray({ control, name: "skills" });
  const skills = watch("skills");

  function rollStatCheck(stat: CyberpunkStat) {
    onRoll?.({ roll_type: "stat_check", context: { ability: stat } });
  }

  function rollSkillCheck(index: number) {
    const skill = skills?.[index];
    if (!skill?.name) return;
    onRoll?.({ roll_type: "skill_check", context: { skill: skill.name } });
  }

  function rollSkillAttack(index: number) {
    const skill = skills?.[index];
    if (!skill?.name) return;
    onRoll?.({ roll_type: "attack_roll", context: { skill: skill.name } });
  }

  function rollInitiative() {
    onRoll?.({ roll_type: "initiative" });
  }

  return (
    <form className="sheet-form" onSubmit={handleSubmit(onSubmit)}>
      <section className="sheet-section">
        <h3>Estadísticas</h3>
        <div className="sheet-abilities">
          {CYBERPUNK_STATS.map((stat) => (
            <div key={stat} className="sheet-ability">
              <label className="form-field">
                <span>{CYBERPUNK_STAT_LABELS[stat]}</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  disabled={disabled}
                  {...register(`stats.${stat}`, { valueAsNumber: true })}
                />
              </label>
              <div className="sheet-ability__footer">
                <RollButton
                  label={`Tirar ${CYBERPUNK_STAT_LABELS[stat]}`}
                  disabled={rollDisabled}
                  onClick={() => rollStatCheck(stat)}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="sheet-section">
        <h3>Salud (HP)</h3>
        <div className="sheet-grid sheet-grid--3">
          <Input
            label="HP máximos"
            type="number"
            min={1}
            disabled={disabled}
            error={errors.hp?.max?.message}
            {...register("hp.max", { valueAsNumber: true })}
          />
          <Input
            label="HP actuales"
            type="number"
            min={0}
            disabled={disabled}
            error={errors.hp?.current?.message}
            {...register("hp.current", { valueAsNumber: true })}
          />
        </div>
      </section>

      <section className="sheet-section">
        <div className="sheet-section__header">
          <h3>Iniciativa</h3>
          <RollButton label="Tirar iniciativa (REF + d10)" disabled={rollDisabled} onClick={rollInitiative} />
        </div>
      </section>

      <section className="sheet-section">
        <h3>Armadura (SP)</h3>
        <div className="sheet-grid sheet-grid--3">
          <Input
            label="Cabeza"
            type="number"
            min={0}
            max={25}
            disabled={disabled}
            error={errors.armor?.head?.message}
            {...register("armor.head", { valueAsNumber: true })}
          />
          <Input
            label="Cuerpo"
            type="number"
            min={0}
            max={25}
            disabled={disabled}
            error={errors.armor?.body?.message}
            {...register("armor.body", { valueAsNumber: true })}
          />
        </div>
      </section>

      <section className="sheet-section">
        <div className="sheet-section__header">
          <h3>Habilidades</h3>
          <Button
            type="button"
            variant="secondary"
            disabled={disabled}
            onClick={() => append({ name: "", stat: "ref", rank: 0 })}
          >
            Añadir habilidad
          </Button>
        </div>
        {fields.length === 0 && <p className="muted">Sin habilidades registradas.</p>}
        {fields.map((field, index) => (
          <div key={field.id} className="sheet-attack">
            <Input
              label="Nombre"
              disabled={disabled}
              error={errors.skills?.[index]?.name?.message}
              {...register(`skills.${index}.name`)}
            />
            <label className="form-field">
              <span>Stat</span>
              <select disabled={disabled} {...register(`skills.${index}.stat`)}>
                {CYBERPUNK_STATS.map((stat) => (
                  <option key={stat} value={stat}>
                    {CYBERPUNK_STAT_LABELS[stat]}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label="Rango"
              type="number"
              min={0}
              max={10}
              disabled={disabled}
              error={errors.skills?.[index]?.rank?.message}
              {...register(`skills.${index}.rank`, { valueAsNumber: true })}
            />
            <div className="sheet-attack__rolls">
              <RollButton
                label={`Tirar ${skills?.[index]?.name || "habilidad"}`}
                disabled={rollDisabled || !skills?.[index]?.name}
                onClick={() => rollSkillCheck(index)}
              />
              <Button
                type="button"
                variant="secondary"
                disabled={rollDisabled || !skills?.[index]?.name}
                onClick={() => rollSkillAttack(index)}
              >
                Tirar ataque
              </Button>
            </div>
            <Button type="button" variant="secondary" disabled={disabled} onClick={() => remove(index)}>
              Quitar
            </Button>
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

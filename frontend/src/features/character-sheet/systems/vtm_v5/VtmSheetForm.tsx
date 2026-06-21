import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Dices } from "lucide-react";

import type { SheetRollRequest } from "../../../../api/types";
import { Button, Input, Tooltip } from "../../../../components/ui";
import {
  VTM_ATTRIBUTE_LABELS,
  VTM_MENTAL_ATTRS,
  VTM_PHYSICAL_ATTRS,
  VTM_SKILL_CATEGORIES,
  VTM_SKILL_CATEGORY_LABELS,
  VTM_SOCIAL_ATTRS,
  vtmV5SheetSchema,
  type VtmAttribute,
  type VtmV5Sheet,
} from "./schema";

type VtmSheetFormProps = {
  defaultValues: VtmV5Sheet;
  onSubmit: (sheet: VtmV5Sheet) => void;
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

function AttributeGroup({
  title,
  attrs,
  register,
  disabled,
  rollDisabled,
  onRollAttribute,
}: {
  title: string;
  attrs: readonly VtmAttribute[];
  register: ReturnType<typeof useForm<VtmV5Sheet>>["register"];
  disabled?: boolean;
  rollDisabled?: boolean;
  onRollAttribute?: (attr: VtmAttribute) => void;
}) {
  return (
    <div className="sheet-subsection">
      <h4>{title}</h4>
      <div className="sheet-abilities">
        {attrs.map((attr) => (
          <div key={attr} className="sheet-ability">
            <label className="form-field">
              <span>{VTM_ATTRIBUTE_LABELS[attr]}</span>
              <input
                type="number"
                min={1}
                max={5}
                disabled={disabled}
                {...register(`attributes.${attr}`, { valueAsNumber: true })}
              />
            </label>
            <div className="sheet-ability__footer">
              <RollButton
                label={`Tirar ${VTM_ATTRIBUTE_LABELS[attr]}`}
                disabled={rollDisabled}
                onClick={() => onRollAttribute?.(attr)}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function VtmSheetForm({
  defaultValues,
  onSubmit,
  onRoll,
  disabled,
  isSaving,
  isRolling,
}: VtmSheetFormProps) {
  const rollDisabled = disabled || isRolling || !onRoll;

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<VtmV5Sheet>({
    resolver: zodResolver(vtmV5SheetSchema),
    defaultValues,
  });

  const skillsField = useFieldArray({ control, name: "skills" });
  const disciplinesField = useFieldArray({ control, name: "disciplines" });
  const skills = watch("skills");
  const disciplines = watch("disciplines");

  function rollAttributeCheck(attribute: VtmAttribute) {
    onRoll?.({ roll_type: "attribute_check", context: { ability: attribute } });
  }

  function rollSkillCheck(index: number) {
    const skill = skills?.[index];
    if (!skill?.name) return;
    onRoll?.({ roll_type: "skill_check", context: { skill: skill.name } });
  }

  function rollDisciplineCheck(index: number) {
    const discipline = disciplines?.[index];
    if (!discipline?.name) return;
    onRoll?.({ roll_type: "discipline_check", context: { skill: discipline.name } });
  }

  function rollRouseCheck() {
    onRoll?.({ roll_type: "rouse_check" });
  }

  return (
    <form className="sheet-form" onSubmit={handleSubmit(onSubmit)}>
      <section className="sheet-section">
        <h3>Atributos</h3>
        <AttributeGroup
          title="Físicos"
          attrs={VTM_PHYSICAL_ATTRS}
          register={register}
          disabled={disabled}
          rollDisabled={rollDisabled}
          onRollAttribute={rollAttributeCheck}
        />
        <AttributeGroup
          title="Sociales"
          attrs={VTM_SOCIAL_ATTRS}
          register={register}
          disabled={disabled}
          rollDisabled={rollDisabled}
          onRollAttribute={rollAttributeCheck}
        />
        <AttributeGroup
          title="Mentales"
          attrs={VTM_MENTAL_ATTRS}
          register={register}
          disabled={disabled}
          rollDisabled={rollDisabled}
          onRollAttribute={rollAttributeCheck}
        />
      </section>

      <section className="sheet-section">
        <div className="sheet-section__header">
          <h3>Salud y hambre</h3>
          <RollButton label="Rouse check" disabled={rollDisabled} onClick={rollRouseCheck} />
        </div>
        <div className="sheet-grid sheet-grid--3">
          <Input
            label="Daño superficial"
            type="number"
            min={0}
            disabled={disabled}
            error={errors.health?.superficial?.message}
            {...register("health.superficial", { valueAsNumber: true })}
          />
          <Input
            label="Daño agravado"
            type="number"
            min={0}
            disabled={disabled}
            error={errors.health?.aggravated?.message}
            {...register("health.aggravated", { valueAsNumber: true })}
          />
          <Input
            label="Salud máxima"
            type="number"
            min={1}
            disabled={disabled}
            error={errors.health?.max?.message}
            {...register("health.max", { valueAsNumber: true })}
          />
          <Input
            label="Hambre"
            type="number"
            min={0}
            max={5}
            disabled={disabled}
            error={errors.hunger?.message}
            {...register("hunger", { valueAsNumber: true })}
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
            onClick={() => skillsField.append({ name: "", category: "physical", dots: 0 })}
          >
            Añadir habilidad
          </Button>
        </div>
        {skillsField.fields.length === 0 && <p className="muted">Sin habilidades registradas.</p>}
        {skillsField.fields.map((field, index) => (
          <div key={field.id} className="sheet-attack">
            <Input
              label="Nombre"
              disabled={disabled}
              error={errors.skills?.[index]?.name?.message}
              {...register(`skills.${index}.name`)}
            />
            <label className="form-field">
              <span>Categoría</span>
              <select disabled={disabled} {...register(`skills.${index}.category`)}>
                {VTM_SKILL_CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {VTM_SKILL_CATEGORY_LABELS[category]}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label="Puntos"
              type="number"
              min={0}
              max={5}
              disabled={disabled}
              error={errors.skills?.[index]?.dots?.message}
              {...register(`skills.${index}.dots`, { valueAsNumber: true })}
            />
            <RollButton
              label={`Tirar ${skills?.[index]?.name || "habilidad"}`}
              disabled={rollDisabled || !skills?.[index]?.name}
              onClick={() => rollSkillCheck(index)}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={disabled}
              onClick={() => skillsField.remove(index)}
            >
              Quitar
            </Button>
          </div>
        ))}
      </section>

      <section className="sheet-section">
        <div className="sheet-section__header">
          <h3>Disciplinas</h3>
          <Button
            type="button"
            variant="secondary"
            disabled={disabled}
            onClick={() => disciplinesField.append({ name: "", level: 1 })}
          >
            Añadir disciplina
          </Button>
        </div>
        {disciplinesField.fields.length === 0 && <p className="muted">Sin disciplinas registradas.</p>}
        {disciplinesField.fields.map((field, index) => (
          <div key={field.id} className="sheet-attack">
            <Input
              label="Nombre"
              disabled={disabled}
              error={errors.disciplines?.[index]?.name?.message}
              {...register(`disciplines.${index}.name`)}
            />
            <Input
              label="Nivel"
              type="number"
              min={1}
              max={5}
              disabled={disabled}
              error={errors.disciplines?.[index]?.level?.message}
              {...register(`disciplines.${index}.level`, { valueAsNumber: true })}
            />
            <RollButton
              label={`Tirar ${disciplines?.[index]?.name || "disciplina"}`}
              disabled={rollDisabled || !disciplines?.[index]?.name}
              onClick={() => rollDisciplineCheck(index)}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={disabled}
              onClick={() => disciplinesField.remove(index)}
            >
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

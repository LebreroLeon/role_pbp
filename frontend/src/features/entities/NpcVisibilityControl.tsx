import {
  NPC_VISIBILITY_LABELS,
  NPC_VISIBILITY_OPTIONS,
  type NpcPlayerVisibility,
} from "./playerVisibility";

type NpcVisibilityControlProps = {
  value: NpcPlayerVisibility;
  onChange: (value: NpcPlayerVisibility) => void;
  disabled?: boolean;
  className?: string;
  compact?: boolean;
};

export function NpcVisibilityControl({
  value,
  onChange,
  disabled,
  className,
  compact,
}: NpcVisibilityControlProps) {
  return (
    <div
      className={`npc-visibility-control${compact ? " npc-visibility-control--compact" : ""}${className ? ` ${className}` : ""}`}
      role="radiogroup"
      aria-label="Visibilidad para jugadores"
    >
      {NPC_VISIBILITY_OPTIONS.map((option) => (
        <button
          key={option}
          type="button"
          role="radio"
          aria-checked={value === option}
          className={`npc-visibility-control__option npc-visibility-control__option--${option}${value === option ? " is-active" : ""}`}
          disabled={disabled}
          onClick={() => onChange(option)}
        >
          {NPC_VISIBILITY_LABELS[option]}
        </button>
      ))}
    </div>
  );
}

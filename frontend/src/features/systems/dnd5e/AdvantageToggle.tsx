import type { AdvantageMode } from "../registry";
import { Tooltip } from "../../../components/ui";

type AdvantageToggleProps = {
  value: AdvantageMode;
  onChange: (mode: AdvantageMode) => void;
  disabled?: boolean;
  compact?: boolean;
};

const OPTIONS: { mode: AdvantageMode; label: string; title: string }[] = [
  { mode: "normal", label: "Normal", title: "Tirada normal (1d20)" },
  { mode: "advantage", label: "Ventaja", title: "Ventaja — 2d20, conservar el mayor" },
  { mode: "disadvantage", label: "Desventaja", title: "Desventaja — 2d20, conservar el menor" },
];

export function AdvantageToggle({ value, onChange, disabled, compact }: AdvantageToggleProps) {
  return (
    <div
      className={`advantage-toggle${compact ? " advantage-toggle--compact" : ""}`}
      role="group"
      aria-label="Ventaja o desventaja"
    >
      {OPTIONS.map((option) => (
        <Tooltip key={option.mode} content={option.title}>
          <button
            type="button"
            className={`advantage-toggle__btn${value === option.mode ? " is-active" : ""}`}
            disabled={disabled}
            aria-pressed={value === option.mode}
            aria-label={option.title}
            onClick={() => onChange(option.mode)}
          >
            {option.label}
          </button>
        </Tooltip>
      ))}
    </div>
  );
}

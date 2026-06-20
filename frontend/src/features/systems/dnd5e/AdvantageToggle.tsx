import type { AdvantageMode } from "../registry";

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
        <button
          key={option.mode}
          type="button"
          className={`advantage-toggle__btn${value === option.mode ? " is-active" : ""}`}
          disabled={disabled}
          title={option.title}
          aria-pressed={value === option.mode}
          onClick={() => onChange(option.mode)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

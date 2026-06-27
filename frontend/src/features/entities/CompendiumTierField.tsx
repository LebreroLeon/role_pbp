import { COMPENDIUM_TIER_LABELS, type CompendiumTier } from "./compendiumTier";

type CompendiumTierFieldProps = {
  value: CompendiumTier;
  onChange: (tier: CompendiumTier) => void;
  disabled?: boolean;
  id?: string;
  /** Inline select for entity list cards (no visible label). */
  compact?: boolean;
  /** Accessible name when compact. */
  ariaLabel?: string;
};

export function CompendiumTierField({
  value,
  onChange,
  disabled,
  id,
  compact = false,
  ariaLabel = "Visible en el compendio",
}: CompendiumTierFieldProps) {
  return (
    <label className={compact ? "entity-card__tier" : "form-field"}>
      {compact ? (
        <span className="sr-only">{ariaLabel}</span>
      ) : (
        <span>Visible en</span>
      )}
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value as CompendiumTier)}
        disabled={disabled}
        aria-label={compact ? ariaLabel : undefined}
      >
        {(Object.keys(COMPENDIUM_TIER_LABELS) as CompendiumTier[]).map((tier) => (
          <option key={tier} value={tier}>
            {COMPENDIUM_TIER_LABELS[tier]}
          </option>
        ))}
      </select>
    </label>
  );
}

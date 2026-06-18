import type { ButtonHTMLAttributes } from "react";

export type SwitchTone = "rose" | "teal";

type SwitchProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onChange" | "role" | "type"> & {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label: string;
  description?: string;
  showState?: boolean;
  tone?: SwitchTone;
};

export function Switch({
  checked,
  onCheckedChange,
  label,
  description,
  showState = true,
  tone = "teal",
  className = "",
  disabled,
  id,
  ...props
}: SwitchProps) {
  const switchId = id ?? `switch-${label.replace(/\s+/g, "-").toLowerCase()}`;

  return (
    <div className={`ui-switch-row ${className}`.trim()}>
      <div className="ui-switch-row__text">
        <label className="ui-switch-row__label" htmlFor={switchId}>
          {label}
        </label>
        {description && <span className="ui-switch-row__desc">{description}</span>}
      </div>
      <div className="ui-switch-row__control">
        {showState && (
          <span className={`ui-switch-row__state ${checked ? "is-on" : "is-off"}`} aria-hidden>
            {checked ? "ON" : "OFF"}
          </span>
        )}
        <button
          {...props}
          id={switchId}
          type="button"
          role="switch"
          aria-checked={checked}
          aria-label={`${label}${description ? `, ${description}` : ""}`}
          disabled={disabled}
          className={`ui-switch ui-switch--${tone} ${checked ? "is-checked" : ""}`.trim()}
          onClick={() => onCheckedChange(!checked)}
        >
          <span className="ui-switch__track" aria-hidden>
            <span className="ui-switch__thumb" />
          </span>
        </button>
      </div>
    </div>
  );
}

import type { ReactNode } from "react";
import { EyeOff } from "lucide-react";

type MasterOnlyFieldProps = {
  label: string;
  htmlFor?: string;
  description?: string;
  children: ReactNode;
  className?: string;
};

export function MasterOnlyField({
  label,
  htmlFor,
  description,
  children,
  className = "",
}: MasterOnlyFieldProps) {
  return (
    <div className={`master-only-field ${className}`.trim()}>
      <div className="master-only-field__header">
        {htmlFor ? (
          <label className="master-only-field__label" htmlFor={htmlFor}>
            {label}
          </label>
        ) : (
          <span className="master-only-field__label">{label}</span>
        )}
        <span className="master-only-field__badge" aria-hidden>
          <EyeOff size={12} />
          Solo Máster
        </span>
      </div>
      {description && <p className="master-only-field__description muted">{description}</p>}
      <div className="master-only-field__content">{children}</div>
    </div>
  );
}

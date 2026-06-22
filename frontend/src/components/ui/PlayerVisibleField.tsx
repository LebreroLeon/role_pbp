import type { ReactNode } from "react";
import { MessageSquare } from "lucide-react";

type PlayerVisibleFieldProps = {
  label: string;
  htmlFor?: string;
  description?: string;
  badgeLabel?: string;
  children: ReactNode;
  className?: string;
};

export function PlayerVisibleField({
  label,
  htmlFor,
  description,
  badgeLabel = "Visible al activar",
  children,
  className = "",
}: PlayerVisibleFieldProps) {
  return (
    <div className={`player-visible-field ${className}`.trim()}>
      <div className="player-visible-field__header">
        {htmlFor ? (
          <label className="player-visible-field__label" htmlFor={htmlFor}>
            {label}
          </label>
        ) : (
          <span className="player-visible-field__label">{label}</span>
        )}
        <span className="player-visible-field__badge" aria-hidden>
          <MessageSquare size={12} />
          {badgeLabel}
        </span>
      </div>
      {description && <p className="player-visible-field__description muted">{description}</p>}
      <div className="player-visible-field__content">{children}</div>
    </div>
  );
}

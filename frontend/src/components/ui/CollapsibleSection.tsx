import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { ChevronDown } from "lucide-react";

type PanelIconTone = "violet" | "rose" | "teal" | "amber";

type CollapsibleSectionProps = {
  title: string;
  description?: string;
  icon?: LucideIcon;
  iconTone?: PanelIconTone;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
};

export function CollapsibleSection({
  title,
  description,
  icon: Icon,
  iconTone = "violet",
  defaultOpen = false,
  children,
  className = "",
}: CollapsibleSectionProps) {
  const classes = ["collapsible-section", "panel", className].filter(Boolean).join(" ");

  return (
    <details className={classes} {...(defaultOpen ? { open: true } : {})}>
      <summary className="collapsible-section__summary">
        <div className="panel-header collapsible-section__header">
          <div className="panel-header__title-row">
            {Icon && (
              <span className={`panel-header__icon panel-header__icon--${iconTone}`} aria-hidden>
                <Icon size={18} strokeWidth={2} />
              </span>
            )}
            <div>
              <h2>{title}</h2>
              {description && <p>{description}</p>}
            </div>
          </div>
          <ChevronDown className="collapsible-section__chevron" size={18} aria-hidden />
        </div>
      </summary>
      <div className="collapsible-section__body">{children}</div>
    </details>
  );
}

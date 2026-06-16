import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

type PanelProps = {
  children: ReactNode;
  className?: string;
};

type PanelIconTone = "violet" | "rose" | "teal" | "amber";

type PanelHeaderProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  icon?: LucideIcon;
  iconTone?: PanelIconTone;
};

export function Panel({ children, className = "" }: PanelProps) {
  const classes = ["panel", className].filter(Boolean).join(" ");
  return <section className={classes}>{children}</section>;
}

export function PanelHeader({ title, description, actions, icon: Icon, iconTone = "violet" }: PanelHeaderProps) {
  return (
    <header className="panel-header">
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
      {actions}
    </header>
  );
}

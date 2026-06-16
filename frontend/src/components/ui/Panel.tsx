import type { ReactNode } from "react";

type PanelProps = {
  children: ReactNode;
  className?: string;
};

type PanelHeaderProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
};

export function Panel({ children, className = "" }: PanelProps) {
  const classes = ["panel", className].filter(Boolean).join(" ");
  return <section className={classes}>{children}</section>;
}

export function PanelHeader({ title, description, actions }: PanelHeaderProps) {
  return (
    <header className="panel-header">
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {actions}
    </header>
  );
}

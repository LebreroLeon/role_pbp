import type { ReactNode } from "react";

type SlideOverProps = {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
};

export function SlideOver({ open, title, description, onClose, children }: SlideOverProps) {
  if (!open) return null;

  return (
    <div className="slide-over-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="slide-over"
        role="dialog"
        aria-modal="true"
        aria-labelledby="slide-over-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="slide-over__header">
          <div>
            <h2 id="slide-over-title">{title}</h2>
            {description && <p className="muted slide-over__description">{description}</p>}
          </div>
          <button type="button" className="slide-over__close" onClick={onClose} aria-label="Cerrar">
            ×
          </button>
        </header>
        <div className="slide-over__body">{children}</div>
      </aside>
    </div>
  );
}

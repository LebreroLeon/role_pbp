import type { ReactNode } from "react";

import { Button } from "./Button";

type ConfirmDialogProps = {
  title: string;
  description: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirming?: boolean;
};

export function ConfirmDialog({
  title,
  description,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  onConfirm,
  onCancel,
  confirming = false,
}: ConfirmDialogProps) {
  return (
    <div className="initiative-modal-backdrop" role="presentation" onClick={onCancel}>
      <div
        className="initiative-modal confirm-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="initiative-modal__header">
          <h2 id="confirm-dialog-title">{title}</h2>
          <button type="button" className="initiative-modal__close" onClick={onCancel} aria-label="Cerrar">
            ×
          </button>
        </header>
        <div className="confirm-dialog__body">{description}</div>
        <footer className="initiative-modal__footer">
          <div className="initiative-modal__buttons">
            <Button variant="secondary" onClick={onCancel} disabled={confirming}>
              {cancelLabel}
            </Button>
            <Button onClick={onConfirm} disabled={confirming}>
              {confirming ? "Procesando…" : confirmLabel}
            </Button>
          </div>
        </footer>
      </div>
    </div>
  );
}

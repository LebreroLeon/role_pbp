import type { ReactNode } from "react";

import { Button } from "./Button";
import { Modal } from "./Modal";

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
    <Modal
      title={title}
      titleId="confirm-dialog-title"
      onClose={onCancel}
      size="md"
      bodyClassName="ui-modal__body--form"
      footer={
        <div className="ui-modal__actions">
          <Button variant="secondary" onClick={onCancel} disabled={confirming}>
            {cancelLabel}
          </Button>
          <Button onClick={onConfirm} disabled={confirming}>
            {confirming ? "Procesando…" : confirmLabel}
          </Button>
        </div>
      }
    >
      {description}
    </Modal>
  );
}

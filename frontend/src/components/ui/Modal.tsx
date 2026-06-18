// Use this for all overlays — don't create one-off modals

import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

import "./Modal.css";

export type ModalSize = "sm" | "md" | "lg";

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

type ModalProps = {
  open?: boolean;
  title?: string;
  titleId?: string;
  /** Replaces the default title + close header. */
  header?: ReactNode;
  onClose: () => void;
  closeOnBackdropClick?: boolean;
  size?: ModalSize;
  blurBackdrop?: boolean;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
};

export function Modal({
  open = true,
  title,
  titleId,
  header,
  onClose,
  closeOnBackdropClick = true,
  size = "md",
  blurBackdrop = false,
  footer,
  children,
  className = "",
  bodyClassName = "",
}: ModalProps) {
  const generatedId = useId();
  const resolvedTitleId = titleId ?? (title ? `${generatedId}-title` : undefined);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;

    const panel = panelRef.current;
    if (!panel) return;

    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;

    const focusable = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
      (element) => element.offsetParent !== null || element === panel,
    );
    (focusable[0] ?? panel).focus();

    const panelElement = panel;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key !== "Tab") return;

      const elements = Array.from(panelElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
        (element) => !element.hasAttribute("disabled") && element.tabIndex !== -1,
      );
      if (elements.length === 0) return;

      const first = elements[0];
      const last = elements[elements.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  function handleBackdropClick() {
    if (closeOnBackdropClick) onClose();
  }

  const panelClassName = [
    "ui-modal-panel",
    "ui-modal__panel",
    `ui-modal-panel--${size}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");
  const bodyClasses = ["ui-modal__body", bodyClassName].filter(Boolean).join(" ");

  return createPortal(
    <div
      className={["ui-modal-backdrop", blurBackdrop ? "ui-modal-backdrop--blur" : ""].filter(Boolean).join(" ")}
      role="presentation"
      onClick={handleBackdropClick}
    >
      <div
        ref={panelRef}
        className={panelClassName}
        role="dialog"
        aria-modal="true"
        aria-labelledby={resolvedTitleId}
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        {header ?? (
          <header className="ui-modal__header">
            {title && (
              <h2 id={resolvedTitleId}>{title}</h2>
            )}
            <button type="button" className="ui-modal__close" onClick={onClose} aria-label="Cerrar">
              ×
            </button>
          </header>
        )}
        <div className={bodyClasses}>{children}</div>
        {footer && <footer className="ui-modal__footer">{footer}</footer>}
      </div>
    </div>,
    document.body,
  );
}

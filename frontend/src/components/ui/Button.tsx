import type { ButtonHTMLAttributes, ReactNode } from "react";

import { useSectionTone } from "./SectionToneContext";
import type { SectionTone } from "./sectionTone";

export type ButtonTone = SectionTone;
export type ButtonVariant = "primary" | "secondary";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  /** Solo para excepciones; por defecto usa el tono de la sección actual. */
  tone?: ButtonTone;
  children: ReactNode;
};

export function buttonClasses({
  variant = "primary",
  tone,
  className = "",
}: {
  variant?: ButtonVariant;
  tone?: ButtonTone;
  className?: string;
}) {
  return ["button", variant === "secondary" ? "secondary" : "", tone ? `button--${tone}` : "", className]
    .filter(Boolean)
    .join(" ");
}

export function Button({ variant = "primary", tone, className = "", children, ...props }: ButtonProps) {
  const sectionTone = useSectionTone();
  const resolvedTone = tone ?? sectionTone;

  return (
    <button className={buttonClasses({ variant, tone: resolvedTone, className })} {...props}>
      {children}
    </button>
  );
}

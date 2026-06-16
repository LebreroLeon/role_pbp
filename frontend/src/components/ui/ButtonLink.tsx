import { Link, useResolvedPath, type LinkProps, type To } from "react-router-dom";

import { buttonClasses, type ButtonTone, type ButtonVariant } from "./Button";
import { useSectionTone } from "./SectionToneContext";
import { getToneFromPath } from "./sectionTone";

type ButtonLinkProps = LinkProps & {
  variant?: ButtonVariant;
  /** Solo para excepciones; por defecto infiere del destino o usa la sección actual. */
  tone?: ButtonTone;
};

function toneFromDestination(to: To, explicit?: ButtonTone): ButtonTone | undefined {
  if (explicit) return explicit;
  if (typeof to === "string") return getToneFromPath(to);
  if (typeof to === "object" && typeof to.pathname === "string") return getToneFromPath(to.pathname);
  return undefined;
}

export function ButtonLink({ variant = "primary", tone, className = "", to, ...props }: ButtonLinkProps) {
  const sectionTone = useSectionTone();
  const resolvedPath = useResolvedPath(to);
  const resolvedTone = tone ?? toneFromDestination(to) ?? getToneFromPath(resolvedPath.pathname) ?? sectionTone;

  return <Link className={buttonClasses({ variant, tone: resolvedTone, className })} to={to} {...props} />;
}

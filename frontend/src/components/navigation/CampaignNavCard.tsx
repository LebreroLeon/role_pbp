import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type NavCardVariant = "play" | "world" | "library" | "desk";

type CampaignNavCardProps = {
  title: string;
  description: string;
  to: string;
  icon: LucideIcon;
  variant?: NavCardVariant;
  accent?: "primary" | "secondary";
};

export function CampaignNavCard({
  title,
  description,
  to,
  icon: Icon,
  variant = "world",
  accent = "secondary",
}: CampaignNavCardProps) {
  return (
    <Link
      className={`nav-card nav-card--${variant} ${accent === "primary" ? "nav-card--primary" : ""}`}
      to={to}
    >
      <span className="nav-card__icon" aria-hidden>
        <Icon size={22} strokeWidth={1.75} />
      </span>
      <strong className="nav-card__title">{title}</strong>
      <p className="nav-card__desc">{description}</p>
      <ChevronRight className="nav-card__cta" size={18} aria-hidden />
    </Link>
  );
}

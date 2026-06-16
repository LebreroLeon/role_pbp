import { Link } from "react-router-dom";

type CampaignNavCardProps = {
  title: string;
  description: string;
  to: string;
  accent?: "primary" | "secondary";
};

export function CampaignNavCard({ title, description, to, accent = "secondary" }: CampaignNavCardProps) {
  return (
    <Link className={`nav-card nav-card--${accent}`} to={to}>
      <strong className="nav-card__title">{title}</strong>
      <p className="nav-card__desc">{description}</p>
      <span className="nav-card__cta">Abrir →</span>
    </Link>
  );
}

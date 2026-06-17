import { Crown, User } from "lucide-react";

import type { CampaignMember } from "../../api/types";
import { StatusBadge } from "../../components/ui";

type CampaignMemberListProps = {
  members: CampaignMember[];
  showEmails?: boolean;
  emptyMessage?: string;
};

function roleLabel(role: CampaignMember["role"]): string {
  return role === "MASTER" ? "Máster" : "Jugador";
}

export function CampaignMemberList({
  members,
  showEmails = false,
  emptyMessage = "Aún no hay nadie más en la campaña.",
}: CampaignMemberListProps) {
  if (members.length === 0) {
    return <p className="muted">{emptyMessage}</p>;
  }

  return (
    <ul className="member-list">
      {members.map((member) => {
        const isMaster = member.role === "MASTER";
        const RoleIcon = isMaster ? Crown : User;
        const initials = member.display_name
          .split(/\s+/)
          .slice(0, 2)
          .map((part) => part[0]?.toUpperCase() ?? "")
          .join("");

        return (
          <li key={member.user_id} className="member-card">
            <span className={`member-card__avatar ${isMaster ? "member-card__avatar--master" : ""}`} aria-hidden>
              {initials || "?"}
            </span>
            <div className="member-card__info">
              <strong>{member.display_name}</strong>
              {showEmails && <span className="muted member-card__email">{member.email}</span>}
            </div>
            <span className="member-card__role">
              <RoleIcon size={14} aria-hidden />
              <StatusBadge label="" value={roleLabel(member.role)} ok={isMaster} />
            </span>
          </li>
        );
      })}
    </ul>
  );
}

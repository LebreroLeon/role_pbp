import { useState } from "react";
import { Crown, User } from "lucide-react";

import type { CampaignMember } from "../../api/types";
import { Button, ConfirmDialog, StatusBadge } from "../../components/ui";

type CampaignMemberListProps = {
  members: CampaignMember[];
  showEmails?: boolean;
  showPresence?: boolean;
  onlineUserIds?: ReadonlySet<string>;
  emptyMessage?: string;
  onRemove?: (userId: string) => void;
};

function roleLabel(role: CampaignMember["role"]): string {
  return role === "MASTER" ? "Máster" : "Jugador";
}

export function CampaignMemberList({
  members,
  showEmails = false,
  showPresence = false,
  onlineUserIds,
  emptyMessage = "Aún no hay nadie más en la campaña.",
  onRemove,
}: CampaignMemberListProps) {
  const [pendingRemove, setPendingRemove] = useState<CampaignMember | null>(null);

  if (members.length === 0) {
    return <p className="muted">{emptyMessage}</p>;
  }

  async function handleConfirmRemove() {
    if (!pendingRemove || !onRemove) return;
    await onRemove(pendingRemove.user_id);
    setPendingRemove(null);
  }

  return (
    <>
      <ul className={`member-list ${onRemove ? "member-list--manageable" : ""}`}>
        {members.map((member) => {
          const isMaster = member.role === "MASTER";
          const RoleIcon = isMaster ? Crown : User;
          const initials = member.display_name
            .split(/\s+/)
            .slice(0, 2)
            .map((part) => part[0]?.toUpperCase() ?? "")
            .join("");

          const isOnline = showPresence && (onlineUserIds?.has(member.user_id) ?? false);

          return (
            <li key={member.user_id} className="member-card">
              <span
                className={`member-card__avatar ${isMaster ? "member-card__avatar--master" : ""}`}
                aria-hidden
              >
                {initials || "?"}
                {showPresence && (
                  <span
                    className={`member-card__presence ${isOnline ? "is-online" : "is-offline"}`}
                    title={isOnline ? "En línea" : "Desconectado"}
                  />
                )}
              </span>
              <div className="member-card__info">
                <strong>{member.display_name}</strong>
                {showEmails && <span className="muted member-card__email">{member.email}</span>}
                {showPresence && (
                  <span className={`member-card__presence-label ${isOnline ? "is-online" : "is-offline"}`}>
                    {isOnline ? "En línea" : "Desconectado"}
                  </span>
                )}
              </div>
              <span className="member-card__role">
                <RoleIcon size={14} aria-hidden />
                <StatusBadge label="" value={roleLabel(member.role)} ok={isMaster} />
              </span>
              {onRemove && member.role === "PLAYER" && (
                <Button
                  type="button"
                  variant="secondary"
                  className="member-card__remove"
                  onClick={() => setPendingRemove(member)}
                >
                  Expulsar
                </Button>
              )}
            </li>
          );
        })}
      </ul>

      {pendingRemove && onRemove && (
        <ConfirmDialog
          title="Expulsar jugador"
          description={
            <>
              <p>
                ¿Expulsar a <strong>{pendingRemove.display_name}</strong> de la campaña?
              </p>
              <p className="muted">Perderá acceso al chat, fichas y escenas de esta campaña.</p>
            </>
          }
          confirmLabel="Expulsar"
          onConfirm={handleConfirmRemove}
          onCancel={() => setPendingRemove(null)}
        />
      )}
    </>
  );
}

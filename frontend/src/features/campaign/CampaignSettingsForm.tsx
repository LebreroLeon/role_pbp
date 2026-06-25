import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { Campaign } from "../../api/types";
import { queryKeys } from "../../api/queryKeys";
import { UserPlus, Users } from "../../components/icons";
import { CollapsibleSection, ErrorBanner } from "../../components/ui";
import { useCampaignMembersQuery } from "../../hooks/queries/useCampaignQueries";
import { useCampaignWs } from "../../providers/CampaignWsContext";
import { CampaignBasicSettingsForm } from "./CampaignBasicSettingsForm";
import { CampaignMemberList } from "./CampaignMemberList";
import { InviteMemberForm } from "./InviteMemberForm";

type CampaignSettingsFormProps = {
  campaignId: string;
  campaign: Campaign | undefined;
};

export function CampaignSettingsForm({ campaignId, campaign }: CampaignSettingsFormProps) {
  const queryClient = useQueryClient();
  const { onlineUserIds } = useCampaignWs();
  const [error, setError] = useState<string | null>(null);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);

  async function handleRemoveMember(userId: string) {
    setError(null);
    try {
      await api.removeCampaignMember(campaignId, userId);
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.members(campaignId) });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo expulsar al jugador");
    }
  }

  return (
    <div className="campaign-settings">
      <CampaignBasicSettingsForm campaignId={campaignId} campaign={campaign} showHeading />
      {error && <ErrorBanner message={error} />}

      <CollapsibleSection
        icon={Users}
        iconTone="violet"
        title="Jugadores"
        description="Participantes con acceso a la campaña."
        defaultOpen
      >
        <CampaignMemberList
          members={members.filter((member) => member.role === "PLAYER")}
          showEmails
          showPresence
          onlineUserIds={onlineUserIds}
          onRemove={handleRemoveMember}
        />
        <div className="campaign-settings__invite">
          <h4 className="campaign-settings__subsection">
            <UserPlus size={16} aria-hidden />
            Invitar jugador
          </h4>
          <p className="muted">Añade participantes por email. Deben tener cuenta en RolePBP.</p>
          <InviteMemberForm campaignId={campaignId} hideHeader />
        </div>
      </CollapsibleSection>
    </div>
  );
}

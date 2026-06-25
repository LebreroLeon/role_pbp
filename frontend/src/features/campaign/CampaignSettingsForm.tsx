import { FormEvent, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { Campaign } from "../../api/types";
import { queryKeys } from "../../api/queryKeys";
import { UserPlus, Users } from "../../components/icons";
import { Button, CollapsibleSection, ErrorBanner, Input } from "../../components/ui";
import { useCampaignMembersQuery } from "../../hooks/queries/useCampaignQueries";
import { useCampaignWs } from "../../providers/CampaignWsContext";
import { gameSystemLabel } from "./gameSystems";
import { CampaignMemberList } from "./CampaignMemberList";
import { InviteMemberForm } from "./InviteMemberForm";

type CampaignSettingsFormProps = {
  campaignId: string;
  campaign: Campaign | undefined;
};

export function CampaignSettingsForm({ campaignId, campaign }: CampaignSettingsFormProps) {
  const queryClient = useQueryClient();
  const { onlineUserIds } = useCampaignWs();
  const [name, setName] = useState(campaign?.name ?? "");
  const [tone, setTone] = useState(campaign?.tone ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);

  useEffect(() => {
    setName(campaign?.name ?? "");
    setTone(campaign?.tone ?? "");
  }, [campaign?.name, campaign?.tone]);

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSavedMessage(null);
    try {
      await api.updateCampaign(campaignId, {
        name: name.trim() || undefined,
        tone: tone.trim(),
      });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.detail(campaignId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.all }),
      ]);
      setSavedMessage("Cambios guardados.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
    } finally {
      setLoading(false);
    }
  }

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
      <h3>Datos de la campaña</h3>
      <p className="muted">
        <strong>Sistema:</strong> {gameSystemLabel(campaign?.game_system)}
      </p>
      <form className="auth-form" onSubmit={handleSave}>
        <Input label="Nombre" value={name} onChange={(event) => setName(event.target.value)} required />
        <Input label="Tono narrativo" value={tone} onChange={(event) => setTone(event.target.value)} />
        {error && <ErrorBanner message={error} />}
        {savedMessage && <p className="muted">{savedMessage}</p>}
        <Button type="submit" disabled={loading}>
          {loading ? "Guardando…" : "Guardar cambios"}
        </Button>
      </form>

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

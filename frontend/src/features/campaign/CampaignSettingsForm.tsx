import { FormEvent, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { Campaign, CampaignMember } from "../../api/types";
import { queryKeys } from "../../api/queryKeys";
import { Button, ErrorBanner, Input } from "../../components/ui";
import { useCampaignWs } from "../../providers/CampaignWsContext";
import { gameSystemLabel } from "./gameSystems";
import { CampaignMemberList } from "./CampaignMemberList";

type CampaignSettingsFormProps = {
  campaignId: string;
  campaign: Campaign | undefined;
};

export function CampaignSettingsForm({ campaignId, campaign }: CampaignSettingsFormProps) {
  const queryClient = useQueryClient();
  const { onlineUserIds } = useCampaignWs();
  const [name, setName] = useState(campaign?.name ?? "");
  const [tone, setTone] = useState(campaign?.tone ?? "");
  const [members, setMembers] = useState<CampaignMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(campaign?.name ?? "");
    setTone(campaign?.tone ?? "");
  }, [campaign?.name, campaign?.tone]);

  useEffect(() => {
    api.listCampaignMembers(campaignId).then(setMembers).catch(() => undefined);
  }, [campaignId]);

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.updateCampaign(campaignId, {
        name: name.trim() || undefined,
        tone: tone.trim(),
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.detail(campaignId) });
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
      setMembers((current) => current.filter((member) => member.user_id !== userId));
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
        <Button type="submit" disabled={loading}>
          {loading ? "Guardando…" : "Guardar cambios"}
        </Button>
      </form>

      <h4>Jugadores</h4>
      <CampaignMemberList
        members={members.filter((member) => member.role === "PLAYER")}
        showEmails
        showPresence
        onlineUserIds={onlineUserIds}
        onRemove={handleRemoveMember}
      />
    </div>
  );
}

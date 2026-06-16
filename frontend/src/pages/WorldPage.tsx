import { useState } from "react";
import { useParams } from "react-router-dom";

import { SECTION_ICONS } from "../components/icons";
import { Panel, PanelHeader } from "../components/ui";
import { CreateEntityForm, EntityList, ImportExportPanel } from "../features/entities";
import { useDeleteEntityMutation } from "../hooks/mutations/useEntityMutations";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";

export function WorldPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const deleteMutation = useDeleteEntityMutation(campaignId);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const isMaster = campaign?.role === "MASTER";

  async function handleDelete(entityId: string) {
    setDeletingId(entityId);
    try {
      await deleteMutation.mutateAsync(entityId);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="world-page">
      <Panel>
        <PanelHeader
          icon={SECTION_ICONS.mundo}
          iconTone="violet"
          title="Mundo"
          description={
            isMaster
              ? "Todo lo que existe en tu campaña: personajes no jugadores, lugares y PJ vinculados a jugadores."
              : "Personajes y lugares que tu PJ conoce. Los secretos del Máster no se muestran aquí."
          }
        />
        <EntityList
          entities={entities}
          isMaster={Boolean(isMaster)}
          onDelete={isMaster ? handleDelete : undefined}
          deletingId={deletingId}
        />
      </Panel>

      {isMaster && (
        <>
          <CreateEntityForm campaignId={campaignId} members={members} />
          <ImportExportPanel campaignId={campaignId} />
        </>
      )}
    </div>
  );
}

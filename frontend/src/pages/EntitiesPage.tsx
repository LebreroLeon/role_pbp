import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorBanner, Panel, PanelHeader } from "../components/ui";
import { CreateEntityForm, EntityList } from "../features/entities";
import { useDeleteEntityMutation } from "../hooks/mutations/useEntityMutations";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";

export function EntitiesPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign, isLoading: campaignLoading, isError: campaignError, error: campaignErr } =
    useCampaignQuery(campaignId);
  const { data: entities, isLoading: entitiesLoading, isError: entitiesError, error: entitiesErr } =
    useEntitiesQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const deleteMutation = useDeleteEntityMutation(campaignId);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  if (campaignLoading || entitiesLoading) {
    return <p className="muted">Cargando entidades...</p>;
  }

  if (campaignError || !campaign) {
    return <ErrorBanner message={campaignErr instanceof Error ? campaignErr.message : "Campaña no encontrada"} />;
  }

  const isMaster = campaign.role === "MASTER";

  async function handleDelete(entityId: string) {
    setDeletingId(entityId);
    try {
      await deleteMutation.mutateAsync(entityId);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="entities-page">
      <Panel>
        <PanelHeader
          title="Entidades de campaña"
          description={
            isMaster
              ? "NPCs, ubicaciones y personajes. El lore secreto solo lo ves tú."
              : "Personajes y lugares conocidos por tu grupo. Sin spoilers del Máster."
          }
          actions={
            <Link className="button secondary" to={`/campaigns/${campaignId}`}>
              Volver al hub
            </Link>
          }
        />

        {entitiesError && (
          <ErrorBanner message={entitiesErr instanceof Error ? entitiesErr.message : "Error al cargar entidades"} />
        )}
        {entities && (
          <EntityList
            entities={entities}
            isMaster={isMaster}
            onDelete={isMaster ? handleDelete : undefined}
            deletingId={deletingId}
          />
        )}
      </Panel>

      {isMaster && <CreateEntityForm campaignId={campaignId} members={members} />}
    </div>
  );
}

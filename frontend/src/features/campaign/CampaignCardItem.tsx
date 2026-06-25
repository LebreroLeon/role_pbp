import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ChevronRight, Crown, Pencil, Scroll, Trash2 } from "lucide-react";

import type { Campaign } from "../../api/types";
import { ConfirmDialog } from "../../components/ui";
import { useDeleteCampaignMutation } from "../../hooks/mutations/useCampaignMutations";
import { useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";
import { CampaignEditModal } from "./CampaignEditModal";
import { CampaignStatusBadges } from "./CampaignStatusBadges";

type CampaignCardItemProps = {
  campaign: Campaign;
};

export function CampaignCardItem({ campaign }: CampaignCardItemProps) {
  const isMaster = campaign.role === "MASTER";
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const deleteMutation = useDeleteCampaignMutation();
  const { data: openScene } = useOpenSceneQuery(campaign.id);

  async function handleDelete() {
    await deleteMutation.mutateAsync(campaign.id);
    setDeleteOpen(false);
    if (location.pathname.startsWith(`/campaigns/${campaign.id}`)) {
      navigate("/", { replace: true });
    }
  }

  return (
    <li>
      <div className="campaign-card">
        <Link to={`/campaigns/${campaign.id}`} className="campaign-card__nav">
          <div className="campaign-card__main">
            <span
              className={`campaign-card__icon ${isMaster ? "campaign-card__icon--master" : ""}`}
              aria-hidden
            >
              {isMaster ? <Crown size={18} strokeWidth={2} /> : <Scroll size={18} strokeWidth={2} />}
            </span>
            <div className="campaign-card__body">
              <strong>{campaign.name}</strong>
              {campaign.tone && <p className="muted">{campaign.tone}</p>}
              <CampaignStatusBadges
                campaign={campaign}
                openScene={openScene}
                className="campaign-card__badges"
              />
            </div>
          </div>
          <ChevronRight className="campaign-card__chevron" size={18} aria-hidden />
        </Link>
        {isMaster && (
          <div className="campaign-card__actions">
            <button
              type="button"
              className="campaign-card__edit"
              aria-label={`Editar campaña ${campaign.name}`}
              onClick={() => setEditOpen(true)}
            >
              <Pencil size={16} strokeWidth={2} aria-hidden />
            </button>
            <button
              type="button"
              className="campaign-card__delete"
              aria-label={`Eliminar campaña ${campaign.name}`}
              onClick={() => setDeleteOpen(true)}
            >
              <Trash2 size={16} strokeWidth={2} aria-hidden />
            </button>
          </div>
        )}
      </div>
      {editOpen && <CampaignEditModal campaign={campaign} onClose={() => setEditOpen(false)} />}
      {deleteOpen && (
        <ConfirmDialog
          title="Eliminar campaña"
          description={
            <>
              <p>
                Se eliminará <strong>{campaign.name}</strong> de forma permanente e irreversible.
              </p>
              <p>
                Se borrarán todas las <strong>escenas</strong> y su historial de chat, todas las{" "}
                <strong>entidades</strong> del mundo, los <strong>documentos</strong> de la biblioteca, el chat{" "}
                <strong>OOC</strong>, la memoria de campaña y los miembros asociados.
              </p>
              <p className="muted">Esta acción no se puede deshacer.</p>
            </>
          }
          confirmLabel="Eliminar campaña"
          onConfirm={handleDelete}
          onCancel={() => setDeleteOpen(false)}
          confirming={deleteMutation.isPending}
        />
      )}
    </li>
  );
}

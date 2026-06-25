import { useId, useState } from "react";

import type { Campaign } from "../../api/types";
import { Button, Modal } from "../../components/ui";
import { CampaignBasicSettingsForm } from "./CampaignBasicSettingsForm";

type CampaignEditModalProps = {
  campaign: Campaign;
  onClose: () => void;
};

export function CampaignEditModal({ campaign, onClose }: CampaignEditModalProps) {
  const formId = useId();
  const [saving, setSaving] = useState(false);

  return (
    <Modal
      title="Editar campaña"
      titleId="campaign-edit-modal-title"
      onClose={onClose}
      size="md"
      bodyClassName="ui-modal__body--form"
      footer={
        <div className="ui-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button type="submit" form={formId} disabled={saving}>
            {saving ? "Guardando…" : "Guardar"}
          </Button>
        </div>
      }
    >
      <CampaignBasicSettingsForm
        campaignId={campaign.id}
        campaign={campaign}
        formId={formId}
        hideSubmitButton
        onPendingChange={setSaving}
        onSaved={onClose}
      />
    </Modal>
  );
}

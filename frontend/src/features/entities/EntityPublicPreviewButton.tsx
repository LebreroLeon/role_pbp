import { useState } from "react";
import { Eye } from "lucide-react";

import { Modal, Tooltip } from "../../components/ui";
import type { CampaignEntity } from "./entityDefaults";
import { EntityIllustrationImage } from "./EntityIllustrationImage";
import {
  extractPublicDescription,
  resolvePublicDisplayName,
  resolvePublicIllustrationUrl,
} from "./entityPublicPreview";

type EntityPublicPreviewButtonProps = {
  entity: CampaignEntity;
  entities: CampaignEntity[];
  isMaster: boolean;
};

export function EntityPublicPreviewButton({ entity, entities, isMaster }: EntityPublicPreviewButtonProps) {
  const [open, setOpen] = useState(false);
  const entityName = resolvePublicDisplayName(entity, entities, isMaster);
  const publicDescription = extractPublicDescription(entity, isMaster);
  const illustrationUrl = resolvePublicIllustrationUrl(entity, isMaster);
  const tooltip = isMaster ? "Vista pública (lo que ven los jugadores)" : "Ver ficha pública";

  return (
    <>
      <Tooltip content={tooltip}>
        <button
          type="button"
          className="entity-illustration-preview-btn entity-illustration-preview-btn--icon"
          onClick={() => setOpen(true)}
          aria-label={`Ver información pública de ${entityName}`}
        >
          <Eye size={14} aria-hidden />
        </button>
      </Tooltip>

      <Modal
        open={open}
        title={entityName}
        onClose={() => setOpen(false)}
        size="lg"
        bodyClassName="entity-public-preview__body"
      >
        {publicDescription ? (
          <p className="entity-public-preview__description">{publicDescription}</p>
        ) : (
          <p className="muted entity-public-preview__empty">Sin descripción pública.</p>
        )}
        {illustrationUrl && (
          <div className="entity-public-preview__illustration">
            <EntityIllustrationImage illustrationUrl={illustrationUrl} alt={`Ilustración de ${entityName}`} />
          </div>
        )}
      </Modal>
    </>
  );
}

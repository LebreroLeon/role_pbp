import { useState } from "react";

import { Button, Modal, Tooltip } from "../../components/ui";
import { extractIllustrationUrl } from "./entityIllustration";
import { EntityIllustrationImage } from "./EntityIllustrationImage";
import type { CampaignEntity } from "./entityDefaults";
import { getEntityDisplayName } from "./entityDefaults";

type EntityIllustrationPreviewButtonProps = {
  entity: CampaignEntity;
  entities: CampaignEntity[];
  compact?: boolean;
};

export function EntityIllustrationPreviewButton({
  entity,
  entities,
  compact = false,
}: EntityIllustrationPreviewButtonProps) {
  const [open, setOpen] = useState(false);
  const illustrationUrl = extractIllustrationUrl(entity);
  const entityName = getEntityDisplayName(entity, entities);

  if (!illustrationUrl) return null;

  return (
    <>
      <Tooltip content="Ver ilustración">
        <Button
          type="button"
          variant="secondary"
          className={compact ? "entity-illustration-preview-btn entity-illustration-preview-btn--compact" : "entity-illustration-preview-btn"}
          onClick={() => setOpen(true)}
          aria-label={`Ver ilustración de ${entityName}`}
        >
          {compact ? "Ver" : "Ilustración"}
        </Button>
      </Tooltip>

      <Modal
        open={open}
        title={`Ilustración — ${entityName}`}
        onClose={() => setOpen(false)}
        size="lg"
        bodyClassName="entity-illustration-preview__body"
      >
        <EntityIllustrationImage illustrationUrl={illustrationUrl} alt={`Ilustración de ${entityName}`} />
      </Modal>
    </>
  );
}

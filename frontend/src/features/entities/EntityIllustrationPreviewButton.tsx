import { useState } from "react";
import { Eye } from "lucide-react";

import { Button, Modal, Tooltip } from "../../components/ui";
import { extractIllustrationUrl } from "./entityIllustration";
import { EntityIllustrationImage } from "./EntityIllustrationImage";
import type { CampaignEntity } from "./entityDefaults";
import { getEntityDisplayName } from "./entityDefaults";

type EntityIllustrationPreviewButtonProps = {
  entity: CampaignEntity;
  entities: CampaignEntity[];
  compact?: boolean;
  iconOnly?: boolean;
};

export function EntityIllustrationPreviewButton({
  entity,
  entities,
  compact = false,
  iconOnly = false,
}: EntityIllustrationPreviewButtonProps) {
  const [open, setOpen] = useState(false);
  const illustrationUrl = extractIllustrationUrl(entity);
  const entityName = getEntityDisplayName(entity, entities);

  if (!illustrationUrl) return null;

  const buttonClassName = [
    "entity-illustration-preview-btn",
    compact ? "entity-illustration-preview-btn--compact" : "",
    iconOnly ? "entity-illustration-preview-btn--icon" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <>
      <Tooltip content="Ver ilustración">
        <Button
          type="button"
          variant="secondary"
          className={buttonClassName}
          onClick={() => setOpen(true)}
          aria-label={`Ver ilustración de ${entityName}`}
        >
          {iconOnly ? <Eye size={14} aria-hidden /> : compact ? "Ver" : "Ilustración"}
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

import type { CampaignEntity, ChatMessage } from "../../api/types";
import { EntityIllustrationPreviewButton } from "../entities/EntityIllustrationPreviewButton";
import {
  canShowIllustrationPreview,
  resolveMessageSpeakerEntity,
} from "../entities/entityIllustration";

type ChatIllustrationPreviewIconProps = {
  message?: ChatMessage;
  entityId?: string;
  entities?: CampaignEntity[];
  isMaster?: boolean;
};

export function ChatIllustrationPreviewIcon({
  message,
  entityId,
  entities,
  isMaster = false,
}: ChatIllustrationPreviewIconProps) {
  if (!entities?.length) return null;

  const entity =
    (message ? resolveMessageSpeakerEntity(message, entities) : undefined) ??
    (entityId ? entities.find((item) => item.id === entityId) : undefined);

  if (!entity || !canShowIllustrationPreview(entity, isMaster)) return null;

  return (
    <EntityIllustrationPreviewButton entity={entity} entities={entities} iconOnly />
  );
}

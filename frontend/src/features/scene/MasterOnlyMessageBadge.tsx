import { EyeOff } from "lucide-react";
import type { ChatMessage } from "../../api/types";
import { Tooltip } from "../../components/ui";
import { masterOnlyBadgeLabel } from "./messageVisibility";

type MasterOnlyMessageBadgeProps = {
  message: ChatMessage;
};

export function MasterOnlyMessageBadge({ message }: MasterOnlyMessageBadgeProps) {
  const label = masterOnlyBadgeLabel(message);

  return (
    <Tooltip content="Solo visible para ti; los jugadores no ven este mensaje">
      <span className="chat-card__master-only-badge" aria-label="Solo visible para ti; los jugadores no ven este mensaje">
        <EyeOff size={12} aria-hidden />
        {label}
      </span>
    </Tooltip>
  );
}

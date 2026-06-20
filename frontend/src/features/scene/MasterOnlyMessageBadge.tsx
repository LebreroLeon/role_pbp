import { EyeOff } from "lucide-react";
import type { ChatMessage } from "../../api/types";
import { masterOnlyBadgeLabel } from "./messageVisibility";

type MasterOnlyMessageBadgeProps = {
  message: ChatMessage;
};

export function MasterOnlyMessageBadge({ message }: MasterOnlyMessageBadgeProps) {
  const label = masterOnlyBadgeLabel(message);

  return (
    <span
      className="chat-card__master-only-badge"
      title="Solo visible para ti; los jugadores no ven este mensaje"
    >
      <EyeOff size={12} aria-hidden />
      {label}
    </span>
  );
}

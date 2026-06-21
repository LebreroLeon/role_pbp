import { Trash2 } from "../../components/icons";
import { Tooltip } from "../../components/ui";

type ChatMessageDeleteButtonProps = {
  onClick: () => void;
};

export function ChatMessageDeleteButton({ onClick }: ChatMessageDeleteButtonProps) {
  return (
    <Tooltip content="Borrar mensaje">
      <button
        type="button"
        className="chat-card__delete"
        onClick={onClick}
        aria-label="Borrar mensaje"
      >
        <Trash2 size={14} aria-hidden />
      </button>
    </Tooltip>
  );
}

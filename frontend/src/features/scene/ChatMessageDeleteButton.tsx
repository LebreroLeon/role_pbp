import { Trash2 } from "../../components/icons";

type ChatMessageDeleteButtonProps = {
  onClick: () => void;
};

export function ChatMessageDeleteButton({ onClick }: ChatMessageDeleteButtonProps) {
  return (
    <button
      type="button"
      className="chat-card__delete"
      onClick={onClick}
      aria-label="Borrar mensaje"
      title="Borrar mensaje"
    >
      <Trash2 size={14} aria-hidden />
    </button>
  );
}

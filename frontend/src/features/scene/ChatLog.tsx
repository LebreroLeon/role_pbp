import type { ChatMessage } from "../../api/types";

type ChatLogProps = {
  messages: ChatMessage[];
  emptyMessage: string;
};

export function ChatLog({ messages, emptyMessage }: ChatLogProps) {
  if (!messages.length) {
    return <p className="muted">{emptyMessage}</p>;
  }

  return (
    <>
      {messages.map((entry, index) => (
        <article key={`${entry.timestamp}-${index}`} className="chat-entry">
          <header>
            <strong>{entry.sender_id}</strong>
            <span>{entry.type}</span>
          </header>
          <p>{entry.text}</p>
        </article>
      ))}
    </>
  );
}

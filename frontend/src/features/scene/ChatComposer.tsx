import { FormEvent } from "react";

import type { MessageType } from "./messageTypes";
import { MESSAGE_TYPE_META } from "./messageTypes";
import { Button } from "../../components/ui";

const PLAYER_TYPES: MessageType[] = ["SPEAK", "ACTION", "CONTEXT"];

type ChatComposerProps = {
  value: string;
  messageType: MessageType;
  onChange: (value: string) => void;
  onTypeChange: (type: MessageType) => void;
  onSubmit: (event: FormEvent) => void;
  disabled: boolean;
  isMaster: boolean;
};

export function ChatComposer({
  value,
  messageType,
  onChange,
  onTypeChange,
  onSubmit,
  disabled,
  isMaster,
}: ChatComposerProps) {
  const types = isMaster ? [...PLAYER_TYPES, "MASTER" as MessageType] : PLAYER_TYPES;
  const meta = MESSAGE_TYPE_META[messageType] ?? MESSAGE_TYPE_META.ACTION;

  return (
    <form className="chat-composer" onSubmit={onSubmit}>
      <div className="chat-composer__modes">
        {types.map((type) => {
          const typeMeta = MESSAGE_TYPE_META[type];
          return (
            <button
              key={type}
              type="button"
              className={`chat-composer__mode chat-composer__mode--${typeMeta.color} ${
                messageType === type ? "is-active" : ""
              }`}
              onClick={() => onTypeChange(type)}
              disabled={disabled}
            >
              {typeMeta.label}
            </button>
          );
        })}
      </div>
      <div className="chat-composer__row">
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={meta.placeholder}
          disabled={disabled}
          rows={2}
        />
        <Button type="submit" disabled={disabled || !value.trim()}>
          Enviar
        </Button>
      </div>
    </form>
  );
}

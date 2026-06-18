import { FormEvent, KeyboardEvent, useMemo, useRef, useState } from "react";

import { Button } from "../../components/ui";
import type { MessageType } from "./messageTypes";
import { MESSAGE_TYPE_META } from "./messageTypes";
import { filterMentionOptions, type MentionOption } from "./mentionOptions";
import { type SpeakerOption } from "./speakerOptions";

const PLAYER_TYPES: MessageType[] = ["SPEAK", "ACTION", "CONTEXT"];

type ChatComposerProps = {
  value: string;
  messageType: MessageType;
  onChange: (value: string) => void;
  onTypeChange: (type: MessageType) => void;
  onSubmit: (event: FormEvent) => void;
  disabled: boolean;
  isMaster: boolean;
  mentionOptions?: MentionOption[];
  speakerOptions?: SpeakerOption[];
  speakerId?: string;
  onSpeakerChange?: (speakerId: string) => void;
};

export function ChatComposer({
  value,
  messageType,
  onChange,
  onTypeChange,
  onSubmit,
  disabled,
  isMaster,
  mentionOptions = [],
  speakerOptions = [],
  speakerId,
  onSpeakerChange,
}: ChatComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);
  const [mentionStart, setMentionStart] = useState<number | null>(null);
  const [activeMentionIndex, setActiveMentionIndex] = useState(0);

  const types = isMaster ? [...PLAYER_TYPES, "MASTER" as MessageType] : PLAYER_TYPES;
  const meta = MESSAGE_TYPE_META[messageType] ?? MESSAGE_TYPE_META.ACTION;
  const showSpeakerSelect = isMaster && speakerOptions.length > 0 && onSpeakerChange;

  const npcOptions = useMemo(
    () => speakerOptions.filter((option) => option.entityType === "NPC"),
    [speakerOptions],
  );
  const pcOptions = useMemo(
    () => speakerOptions.filter((option) => option.entityType === "PC"),
    [speakerOptions],
  );
  const narratorOption = speakerOptions.find((option) => option.speakerType === "NARRATOR");

  const filteredMentions = useMemo(() => {
    if (mentionQuery === null) return [];
    return filterMentionOptions(mentionOptions, mentionQuery);
  }, [mentionOptions, mentionQuery]);

  const showMentionPicker = mentionQuery !== null && filteredMentions.length > 0;

  function updateMentionState(text: string, cursor: number) {
    const beforeCursor = text.slice(0, cursor);
    const atMatch = beforeCursor.match(/@([^\s@]*)$/);
    if (!atMatch) {
      setMentionQuery(null);
      setMentionStart(null);
      setActiveMentionIndex(0);
      return;
    }

    setMentionQuery(atMatch[1]);
    setMentionStart(cursor - atMatch[0].length);
    setActiveMentionIndex(0);
  }

  function handleChange(text: string) {
    onChange(text);
    const cursor = textareaRef.current?.selectionStart ?? text.length;
    updateMentionState(text, cursor);
  }

  function applyMention(option: MentionOption) {
    if (mentionStart == null) return;

    const cursor = textareaRef.current?.selectionStart ?? value.length;
    const before = value.slice(0, mentionStart);
    const after = value.slice(cursor);
    const mentionText = `@${option.label}`;
    const spacer = after.startsWith(" ") || after.length === 0 ? "" : " ";
    const nextValue = `${before}${mentionText}${spacer}${after}`;

    onChange(nextValue);
    setMentionQuery(null);
    setMentionStart(null);
    setActiveMentionIndex(0);

    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      const nextCursor = before.length + mentionText.length + spacer.length;
      el.focus();
      el.setSelectionRange(nextCursor, nextCursor);
    });
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (!showMentionPicker) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveMentionIndex((index) => (index + 1) % filteredMentions.length);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveMentionIndex((index) => (index - 1 + filteredMentions.length) % filteredMentions.length);
      return;
    }

    if (event.key === "Enter" || event.key === "Tab") {
      event.preventDefault();
      const option = filteredMentions[activeMentionIndex];
      if (option) applyMention(option);
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      setMentionQuery(null);
      setMentionStart(null);
    }
  }

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
      {showSpeakerSelect && (
        <div className="chat-composer__speaker">
          <label className="chat-composer__speaker-label" htmlFor="chat-speaker-select">
            Hablar como
          </label>
          <select
            id="chat-speaker-select"
            className="chat-composer__speaker-select"
            value={speakerId ?? narratorOption?.id ?? ""}
            onChange={(event) => onSpeakerChange(event.target.value)}
            disabled={disabled}
          >
            {narratorOption && (
              <option value={narratorOption.id}>{narratorOption.label}</option>
            )}
            {npcOptions.length > 0 && (
              <optgroup label="NPCs">
                {npcOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </optgroup>
            )}
            {pcOptions.length > 0 && (
              <optgroup label="Personajes">
                {pcOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>
      )}
      <div className="chat-composer__row">
        <div className="chat-composer__input-wrap">
          {showMentionPicker && (
            <ul className="mention-picker" role="listbox" aria-label="Menciones">
              {filteredMentions.map((option, index) => (
                <li key={`${option.id}-${option.label}`}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={index === activeMentionIndex}
                    className={`mention-picker__option ${index === activeMentionIndex ? "is-active" : ""}`}
                    onMouseDown={(event) => {
                      event.preventDefault();
                      applyMention(option);
                    }}
                  >
                    <span className="mention-picker__label">@{option.label}</span>
                    {option.entityType && (
                      <span className="mention-picker__tag">{option.entityType}</span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => handleChange(event.target.value)}
            onKeyDown={handleKeyDown}
            onClick={(event) => updateMentionState(value, event.currentTarget.selectionStart)}
            placeholder={meta.placeholder}
            disabled={disabled}
            rows={2}
          />
        </div>
        <Button type="submit" disabled={disabled || !value.trim()}>
          Enviar
        </Button>
      </div>
      <p className="chat-composer__hints muted">
        Usa el panel <strong>Combate rápido</strong> para atacar con la UI.
        {" · "}
        También: <code>@atacante ataca @objetivo</code>
        {" · "}
        <code>@asistente tu pregunta</code> consulta lore (pool limitado)
        {" · "}
        <code>@</code> para mencionar entidades
      </p>
    </form>
  );
}

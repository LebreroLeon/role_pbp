export type MessageType = "SPEAK" | "ACTION" | "CONTEXT" | "MASTER" | "DICE_ROLL" | "NARRATIVE";

export type ChatMessage = {
  id?: string;
  timestamp: string;
  sender_id: string;
  type: MessageType | string;
  text?: string;
  dice_expression?: string;
  raw_result?: number;
  final_result?: number;
  skill_checked?: string | null;
  read_by?: string[];
};

export const MESSAGE_TYPE_META: Record<
  string,
  { label: string; color: string; placeholder: string }
> = {
  SPEAK: {
    label: "Diálogo",
    color: "speak",
    placeholder: "¿Qué dice tu personaje?",
  },
  ACTION: {
    label: "Acción",
    color: "action",
    placeholder: "¿Qué hace tu personaje?",
  },
  CONTEXT: {
    label: "Contexto",
    color: "context",
    placeholder: "Pensamientos, sensaciones o detalle narrativo...",
  },
  MASTER: {
    label: "Máster",
    color: "master",
    placeholder: "Narración o consecuencias del Máster...",
  },
  DICE_ROLL: {
    label: "Tirada",
    color: "dice",
    placeholder: "",
  },
  NARRATIVE: {
    label: "Acción",
    color: "action",
    placeholder: "¿Qué hace tu personaje?",
  },
};

export function normalizeMessageType(type: string): string {
  return type === "NARRATIVE" ? "ACTION" : type;
}

export function formatChatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  const month = date.toLocaleString("en-US", { month: "short" }).toUpperCase();
  const day = date.getDate();
  const time = date.toLocaleString("es-ES", { hour: "numeric", minute: "2-digit", hour12: true });
  return `${month} ${day} · ${time}`;
}

export function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

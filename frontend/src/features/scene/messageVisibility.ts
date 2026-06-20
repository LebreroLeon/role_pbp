import type { ChatMessage } from "../../api/types";

export function isMasterOnlyMessage(message: ChatMessage): boolean {
  return message.visibility === "master_only";
}

export function masterOnlyBadgeLabel(message: ChatMessage): string {
  if (message.type === "DICE_ROLL") return "Tirada en secreto";
  return "Oculta · solo tú";
}

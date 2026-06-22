import type { CampaignMember, OocMessage } from "../../api/types";

export type OocChannelId = "all" | "master" | string;

export type OocChannelTab = {
  id: OocChannelId;
  label: string;
};

export function findMasterMembers(members: CampaignMember[]): CampaignMember[] {
  return members.filter((member) => member.role === "MASTER");
}

export function findPlayerMembers(members: CampaignMember[]): CampaignMember[] {
  return members.filter((member) => member.role === "PLAYER");
}

export function buildOocChannelTabs(
  members: CampaignMember[],
  viewerRole: "MASTER" | "PLAYER",
): OocChannelTab[] {
  const tabs: OocChannelTab[] = [{ id: "all", label: "Todos" }];

  if (viewerRole === "MASTER") {
    for (const player of findPlayerMembers(members)) {
      tabs.push({ id: player.user_id, label: player.display_name });
    }
    return tabs;
  }

  tabs.push({ id: "master", label: "Máster" });
  return tabs;
}

export function messageMatchesChannel(
  message: OocMessage,
  channel: OocChannelId,
  currentUserId: string,
  masterUserIds: string[],
): boolean {
  if (channel === "all") {
    return message.message_type === "OOC_PUBLIC";
  }

  if (message.message_type !== "OOC_WHISPER" || !message.target_user_id) {
    return false;
  }

  const participants = new Set([message.author_user_id, message.target_user_id]);

  if (channel === "master") {
    return participants.has(currentUserId) && masterUserIds.some((id) => participants.has(id));
  }

  return participants.has(currentUserId) && participants.has(channel);
}

export function filterMessagesByChannel(
  messages: OocMessage[],
  channel: OocChannelId,
  currentUserId: string,
  masterUserIds: string[],
): OocMessage[] {
  return messages.filter((message) =>
    messageMatchesChannel(message, channel, currentUserId, masterUserIds),
  );
}

export function resolveWhisperTarget(
  channel: OocChannelId,
  masterUserIds: string[],
): string | null {
  if (channel === "all") {
    return null;
  }
  if (channel === "master") {
    return masterUserIds[0] ?? null;
  }
  return channel;
}

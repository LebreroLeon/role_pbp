import type { Scene } from "../../api/types";

export function campaignDefaultPath(
  campaignId: string,
  role: "MASTER" | "PLAYER",
  openScene?: Pick<Scene, "status"> | null,
): string {
  const base = `/campaigns/${campaignId}`;
  if (role === "MASTER") return `${base}/mundo`;
  if (openScene?.status === "ACTIVE") return `${base}/chat`;
  return `${base}/mundo`;
}

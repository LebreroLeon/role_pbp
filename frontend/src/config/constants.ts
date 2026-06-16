/**
 * Dev-only placeholders until Phase 1 (auth + campaign context).
 * Pages must receive campaign/scene IDs from route params, hooks or API — never inline UUIDs.
 */
export const DEV_PLACEHOLDERS = {
  campaignId: "00000000-0000-4000-8000-000000000001",
  sceneId: "00000000-0000-4000-8000-000000000002",
  senderId: "player_1",
} as const;

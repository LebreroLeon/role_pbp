export const queryKeys = {
  health: ["health"] as const,
  auth: {
    me: ["auth", "me"] as const,
  },
  campaigns: {
    all: ["campaigns"] as const,
    detail: (id: string) => ["campaigns", id] as const,
    members: (id: string) => ["campaigns", id, "members"] as const,
  },
  scenes: {
    detail: (id: string) => ["scenes", id] as const,
  },
  entities: {
    list: (campaignId: string, entityType?: string) =>
      entityType ? (["entities", campaignId, entityType] as const) : (["entities", campaignId] as const),
    detail: (id: string) => ["entities", id] as const,
  },
} as const;

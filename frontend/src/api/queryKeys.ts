export const queryKeys = {
  health: ["health"] as const,
  auth: {
    me: ["auth", "me"] as const,
  },
  campaigns: {
    all: ["campaigns"] as const,
    detail: (id: string) => ["campaigns", id] as const,
    members: (id: string) => ["campaigns", id, "members"] as const,
    activeScene: (id: string) => ["campaigns", id, "scenes", "active"] as const,
    scenes: (id: string) => ["campaigns", id, "scenes"] as const,
  },
  scenes: {
    detail: (id: string) => ["scenes", id] as const,
  },
  documents: {
    all: (campaignId: string) => ["documents", campaignId] as const,
  },
  entities: {
    all: (campaignId: string) => ["entities", campaignId] as const,
    detail: (id: string) => ["entities", id] as const,
    mySheet: (campaignId: string) => ["entities", campaignId, "mine"] as const,
    campaignSheets: (campaignId: string) => ["entities", campaignId, "sheets"] as const,
  },
  systemManuals: {
    status: (systemId: string) => ["system-manuals", systemId, "status"] as const,
  },
} as const;

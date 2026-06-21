import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";

export function useMonsterCatalogSearchQuery(systemId: string, query: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.monsterCatalog.search(systemId, query),
    queryFn: () => api.searchMonsterCatalog(systemId, query),
    enabled: enabled && query.trim().length > 0,
    staleTime: 60_000,
  });
}

export function useSpawnMonstersMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { slug: string; count: number; hidden?: boolean }) =>
      api.spawnMonsters(campaignId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.campaignSheets(campaignId) });
    },
  });
}

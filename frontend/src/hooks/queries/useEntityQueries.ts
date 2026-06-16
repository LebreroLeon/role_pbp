import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

export function useEntitiesQuery(campaignId: string) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.entities.all(campaignId),
    queryFn: () => api.listEntities(campaignId),
    enabled: isAuthenticated && Boolean(campaignId),
  });
}

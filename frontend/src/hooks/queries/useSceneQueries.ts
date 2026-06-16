import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

export function useActiveSceneQuery(campaignId: string) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.campaigns.activeScene(campaignId),
    queryFn: () => api.getActiveScene(campaignId),
    enabled: isAuthenticated && Boolean(campaignId),
    retry: false,
  });
}

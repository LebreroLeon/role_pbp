import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

export function useUnreadCountsQuery(campaignId: string) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.campaigns.unreadCounts(campaignId),
    queryFn: () => api.getUnreadCounts(campaignId),
    enabled: isAuthenticated && Boolean(campaignId),
    staleTime: 15_000,
  });
}

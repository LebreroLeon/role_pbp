import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

export function useCampaignSheetsQuery(campaignId: string, enabled = true) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.entities.campaignSheets(campaignId),
    queryFn: () => api.listCampaignSheets(campaignId),
    enabled: isAuthenticated && Boolean(campaignId) && enabled,
  });
}

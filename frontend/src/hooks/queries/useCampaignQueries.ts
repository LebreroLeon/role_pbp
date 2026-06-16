import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

export function useMeQuery() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: () => api.me(),
    enabled: isAuthenticated,
    retry: false,
  });
}

export function useCampaignsQuery() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.campaigns.all,
    queryFn: () => api.listCampaigns(),
    enabled: isAuthenticated,
  });
}

export function useCampaignQuery(campaignId: string) {
  return useQuery({
    queryKey: queryKeys.campaigns.detail(campaignId),
    queryFn: () => api.getCampaign(campaignId),
    enabled: Boolean(campaignId),
  });
}

export function useCampaignMembersQuery(campaignId: string) {
  return useQuery({
    queryKey: queryKeys.campaigns.members(campaignId),
    queryFn: () => api.listCampaignMembers(campaignId),
    enabled: Boolean(campaignId),
  });
}

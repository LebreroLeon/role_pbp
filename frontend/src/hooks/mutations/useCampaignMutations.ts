import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, type CreateCampaignPayload, type InviteMemberPayload } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";

export function useCreateCampaignMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateCampaignPayload) => api.createCampaign(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.all });
    },
  });
}

export function useInviteMemberMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: InviteMemberPayload) => api.inviteMember(campaignId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.members(campaignId) });
    },
  });
}

export function useUpdateCampaignMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { name?: string; tone?: string }) => api.updateCampaign(campaignId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.detail(campaignId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.all });
    },
  });
}

export function useDeleteCampaignMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => api.deleteCampaign(campaignId),
    onSuccess: (_data, campaignId) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.all });
      queryClient.removeQueries({ queryKey: queryKeys.campaigns.detail(campaignId) });
      queryClient.removeQueries({ queryKey: queryKeys.campaigns.members(campaignId) });
      queryClient.removeQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
      queryClient.removeQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
      queryClient.removeQueries({ queryKey: queryKeys.entities.all(campaignId) });
      queryClient.removeQueries({ queryKey: queryKeys.documents.all(campaignId) });
    },
  });
}

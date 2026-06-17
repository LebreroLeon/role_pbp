import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, type CreateEntityPayload } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";

export function useCreateEntityMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateEntityPayload) => api.createEntity(campaignId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.campaignSheets(campaignId) });
    },
  });
}

export function useDeleteEntityMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entityId: string) => api.deleteEntity(entityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.campaignSheets(campaignId) });
    },
  });
}

export function useUpdateEntityMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ entityId, document }: { entityId: string; document: Record<string, unknown> }) =>
      api.updateEntity(entityId, { document }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.campaignSheets(campaignId) });
    },
  });
}

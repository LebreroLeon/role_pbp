import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, type CreateEntityPayload } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { CampaignEntity } from "../../features/entities/entityDefaults";

function patchEntityInList(list: CampaignEntity[] | undefined, updated: CampaignEntity) {
  if (!list) return list;
  return list.map((entity) => (entity.id === updated.id ? updated : entity));
}

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
    onSuccess: (updatedEntity) => {
      queryClient.setQueryData<CampaignEntity[]>(queryKeys.entities.all(campaignId), (old) =>
        patchEntityInList(old, updatedEntity),
      );
      queryClient.setQueryData<CampaignEntity[]>(queryKeys.entities.campaignSheets(campaignId), (old) =>
        patchEntityInList(old, updatedEntity),
      );
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.campaignSheets(campaignId) });
    },
  });
}

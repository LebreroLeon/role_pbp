import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { CampaignEntity } from "../../features/entities/entityDefaults";

function patchEntityInList(list: CampaignEntity[] | undefined, updated: CampaignEntity) {
  if (!list) return list;
  return list.map((entity) => (entity.id === updated.id ? updated : entity));
}

export function useUploadEntityAvatarMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ entityId, file }: { entityId: string; file: File }) =>
      api.uploadEntityAvatar(entityId, file),
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

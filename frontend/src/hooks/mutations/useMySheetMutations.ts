import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { CharacterSheetUpsert, SheetRollRequest } from "../../api/types";
import { queryKeys } from "../../api/queryKeys";

export function useUpsertMySheetMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CharacterSheetUpsert) => api.upsertMySheet(campaignId, payload),
    onSuccess: (entity) => {
      queryClient.setQueryData(queryKeys.entities.mySheet(campaignId), entity);
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
    },
  });
}

export function useRollFromSheetMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SheetRollRequest) => api.rollFromMySheet(campaignId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
    },
  });
}

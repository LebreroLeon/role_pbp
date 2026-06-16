import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { EntityExportBundle } from "../../api/types";
import { queryKeys } from "../../api/queryKeys";

export function useImportEntitiesMutation(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (entities: EntityExportBundle["entities"]) => api.importEntities(campaignId, entities),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
    },
  });
}

import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";

export function useOocMessagesQuery(campaignId: string) {
  return useQuery({
    queryKey: queryKeys.campaigns.oocMessages(campaignId),
    queryFn: () => api.listOocMessages(campaignId),
    enabled: Boolean(campaignId),
  });
}

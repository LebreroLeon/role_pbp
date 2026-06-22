import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";

export function useOocMessagesQuery(campaignId: string, channel = "all") {
  return useQuery({
    queryKey: queryKeys.campaigns.oocMessages(campaignId, channel),
    queryFn: () => api.listOocMessages(campaignId, channel),
    enabled: Boolean(campaignId),
  });
}

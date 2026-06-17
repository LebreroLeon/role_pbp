import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { ApiError } from "../../api/http";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

export function useMySheetQuery(campaignId: string) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.entities.mySheet(campaignId),
    queryFn: async () => {
      try {
        return await api.getMySheet(campaignId);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
    enabled: isAuthenticated && Boolean(campaignId),
  });
}

import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";

export function useSystemManualStatusQuery(systemId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.systemManuals.status(systemId ?? ""),
    queryFn: () => api.getSystemManualStatus(systemId!),
    enabled: Boolean(systemId),
  });
}

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { Scene } from "../../api/types";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

function pickOpenScene(activeScene: Scene | undefined, scenes: Scene[] | undefined): Scene | null {
  if (activeScene) return activeScene;
  const open = (scenes ?? []).filter((scene) => scene.status === "ACTIVE" || scene.status === "PAUSED");
  if (open.length === 0) return null;
  return open.reduce((latest, scene) => {
    const latestNum = latest.scene_number ?? -1;
    const sceneNum = scene.scene_number ?? -1;
    return sceneNum > latestNum ? scene : latest;
  });
}

export function useActiveSceneQuery(campaignId: string) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.campaigns.activeScene(campaignId),
    queryFn: () => api.getActiveScene(campaignId),
    enabled: isAuthenticated && Boolean(campaignId),
    retry: false,
  });
}

export function useCampaignScenesQuery(campaignId: string) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return useQuery({
    queryKey: queryKeys.campaigns.scenes(campaignId),
    queryFn: () => api.listCampaignScenes(campaignId),
    enabled: isAuthenticated && Boolean(campaignId),
  });
}

/** Escena abierta (ACTIVE o PAUSED). Fallback cuando `/scenes/active` devuelve 404 tras congelar. */
export function useOpenSceneQuery(campaignId: string) {
  const activeQuery = useActiveSceneQuery(campaignId);
  const scenesQuery = useCampaignScenesQuery(campaignId);

  const data = useMemo(
    () => pickOpenScene(activeQuery.data, scenesQuery.data),
    [activeQuery.data, scenesQuery.data],
  );

  return {
    data,
    isLoading: activeQuery.isLoading || scenesQuery.isLoading,
    refetch: async () => {
      await Promise.all([activeQuery.refetch(), scenesQuery.refetch()]);
    },
  };
}

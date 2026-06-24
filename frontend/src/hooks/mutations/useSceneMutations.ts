import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { CombatAttackRequest, Scene, ScenePresenceUpdate, SceneTurnManagementUpdate } from "../../api/types";
import { normalizeScene } from "../../features/scene/sceneState";

type SceneMutationOptions = {
  campaignId: string;
  onSceneUpdate?: (scene: Scene) => void;
};

export function useRollCombatInitiativeMutation({
  campaignId,
  onSceneUpdate,
}: SceneMutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sceneId,
      activateCombat = true,
      entityIds,
    }: {
      sceneId: string;
      activateCombat?: boolean;
      entityIds?: string[];
    }) => api.rollCombatInitiative(sceneId, { activateCombat, entityIds }),
    onSuccess: (scene) => {
      const normalized = normalizeScene(scene);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), normalized);
      queryClient.invalidateQueries({ queryKey: queryKeys.scenes.detail(scene.id) });
      onSceneUpdate?.(normalized);
    },
  });
}

export function useUpdateSceneTurnManagementMutation({
  campaignId,
  onSceneUpdate,
}: SceneMutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sceneId,
      ...payload
    }: SceneTurnManagementUpdate & { sceneId: string }) =>
      api.updateSceneTurnManagement(sceneId, payload),
    onSuccess: (scene) => {
      const normalized = normalizeScene(scene);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), normalized);
      queryClient.invalidateQueries({ queryKey: queryKeys.scenes.detail(scene.id) });
      onSceneUpdate?.(normalized);
    },
  });
}

export function useAdvancePbpTurnMutation({ campaignId, onSceneUpdate }: SceneMutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sceneId }: { sceneId: string }) => api.advancePbpTurn(sceneId),
    onSuccess: (scene) => {
      const normalized = normalizeScene(scene);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), normalized);
      queryClient.invalidateQueries({ queryKey: queryKeys.scenes.detail(scene.id) });
      onSceneUpdate?.(normalized);
    },
  });
}

type CombatAttackVariables = CombatAttackRequest & { sceneId: string };

export function useCombatAttackMutation({ campaignId, onSceneUpdate }: SceneMutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sceneId, ...payload }: CombatAttackVariables) => api.combatAttack(sceneId, payload),
    onSuccess: (scene) => {
      const normalized = normalizeScene(scene);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), normalized);
      queryClient.invalidateQueries({ queryKey: queryKeys.scenes.detail(scene.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      onSceneUpdate?.(normalized);
    },
  });
}

type ScenePresenceVariables = ScenePresenceUpdate & { sceneId: string };

export function useScenePresenceMutation({ campaignId, onSceneUpdate }: SceneMutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sceneId, ...payload }: ScenePresenceVariables) => api.updateScenePresence(sceneId, payload),
    onSuccess: async (scene) => {
      const normalized = normalizeScene(scene);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), normalized);
      queryClient.invalidateQueries({ queryKey: queryKeys.scenes.detail(scene.id) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      onSceneUpdate?.(normalized);
    },
  });
}

type SceneAddPlayerVariables = { sceneId: string; entity_id?: string; user_id?: string };

export function useAddPlayerToSceneMutation({ campaignId, onSceneUpdate }: SceneMutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sceneId, ...payload }: SceneAddPlayerVariables) => api.addPlayerToScene(sceneId, payload),
    onSuccess: async (scene) => {
      const normalized = normalizeScene(scene);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), normalized);
      queryClient.invalidateQueries({ queryKey: queryKeys.scenes.detail(scene.id) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      onSceneUpdate?.(normalized);
    },
  });
}

export function useUpdateSceneScratchpadMutation({ campaignId, onSceneUpdate }: SceneMutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sceneId,
      master_scene_scratchpad,
    }: {
      sceneId: string;
      master_scene_scratchpad: string | null;
    }) => api.updateSceneScratchpad(sceneId, { master_scene_scratchpad }),
    onSuccess: (scene) => {
      const normalized = normalizeScene(scene);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), normalized);
      queryClient.invalidateQueries({ queryKey: queryKeys.scenes.detail(scene.id) });
      onSceneUpdate?.(normalized);
    },
  });
}
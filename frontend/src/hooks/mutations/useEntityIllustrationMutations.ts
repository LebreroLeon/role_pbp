import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { CampaignEntity } from "../../features/entities/entityDefaults";

function patchEntityInList(list: CampaignEntity[] | undefined, updated: CampaignEntity) {
  if (!list) return list;
  return list.map((entity) => (entity.id === updated.id ? updated : entity));
}

export function useUploadEntityIllustrationMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ entityId, file }: { entityId: string; file: File }) =>
      api.uploadEntityIllustration(entityId, file),
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

export function useRemoveEntityIllustrationMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entityId: string) => api.removeEntityIllustration(entityId),
    onSuccess: (_result, entityId) => {
      queryClient.setQueryData<CampaignEntity[]>(queryKeys.entities.all(campaignId), (old) =>
        old?.map((entity) => {
          if (entity.id !== entityId) return entity;
          const document = structuredClone(entity.document);
          clearIllustrationUrlFromDocument(document, entity.entity_type);
          return { ...entity, document };
        }),
      );
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
    },
  });
}

function clearIllustrationUrlFromDocument(document: Record<string, unknown>, entityType: CampaignEntity["entity_type"]) {
  if (entityType === "PC") {
    const profile = document.public_profile as Record<string, unknown> | undefined;
    if (profile) delete profile.illustration_url;
    return;
  }
  if (entityType === "NPC") {
    const profile = document.ai_narrative_profile as Record<string, unknown> | undefined;
    if (profile) delete profile.illustration_url;
    return;
  }
  if (entityType === "LOCATION" || entityType === "FACTION") {
    const profile = document.narrative_profile as Record<string, unknown> | undefined;
    if (profile) delete profile.illustration_url;
    return;
  }
  if (entityType === "RELATIONSHIP") {
    const bond = document.narrative_bond as Record<string, unknown> | undefined;
    if (bond) delete bond.illustration_url;
  }
}

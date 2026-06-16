import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type DocumentType } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";

export function useDocumentsQuery(campaignId: string) {
  return useQuery({
    queryKey: queryKeys.documents.all(campaignId),
    queryFn: () => api.listDocuments(campaignId),
    enabled: Boolean(campaignId),
  });
}

export function useUploadDocumentMutation(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, documentType }: { file: File; documentType: DocumentType }) =>
      api.uploadDocument(campaignId, file, documentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all(campaignId) });
    },
  });
}

export function useDeleteDocumentMutation(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => api.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all(campaignId) });
    },
  });
}

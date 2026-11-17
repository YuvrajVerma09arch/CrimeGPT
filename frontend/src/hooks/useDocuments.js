import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentService } from "../services/documentService";

export function useDocuments(caseId) {
  return useQuery({
    queryKey: ["documents", caseId],
    queryFn: () => documentService.list(caseId),
    enabled: Boolean(caseId),
  });
}

export function useGenerateDocuments(caseId) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docTypes) => documentService.generate(caseId, docTypes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents", caseId] });
      qc.invalidateQueries({ queryKey: ["diary", caseId] });
    },
  });
}

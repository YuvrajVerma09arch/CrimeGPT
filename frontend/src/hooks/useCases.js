import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { caseService } from "../services/caseService";

export function useCases(filters = {}) {
  return useQuery({
    queryKey: ["cases", filters],
    queryFn: () => caseService.list(filters),
  });
}

export function useCase(id) {
  return useQuery({
    queryKey: ["cases", "detail", id],
    queryFn: () => caseService.get(id),
    enabled: Boolean(id),
  });
}

export function useSearchCases(q) {
  return useQuery({
    queryKey: ["cases", "search", q],
    queryFn: () => caseService.search(q),
    enabled: q.trim().length >= 2,
  });
}

export function useCaseDiary(caseId) {
  return useQuery({
    queryKey: ["diary", caseId],
    queryFn: () => caseService.diary(caseId),
    enabled: Boolean(caseId),
  });
}

function useInvalidateCase() {
  const qc = useQueryClient();
  return (caseId) => {
    qc.invalidateQueries({ queryKey: ["cases"] });
    qc.invalidateQueries({ queryKey: ["audit"] });
    if (caseId) qc.invalidateQueries({ queryKey: ["diary", caseId] });
  };
}

export function useCreateCase() {
  const invalidate = useInvalidateCase();
  return useMutation({
    mutationFn: (payload) => caseService.create(payload),
    onSuccess: () => invalidate(),
  });
}

export function useUpdateCase(caseId) {
  const invalidate = useInvalidateCase();
  return useMutation({
    mutationFn: (payload) => caseService.update(caseId, payload),
    onSuccess: () => invalidate(caseId),
  });
}

export function useDeleteCase() {
  const invalidate = useInvalidateCase();
  return useMutation({
    mutationFn: (caseId) => caseService.remove(caseId),
    onSuccess: () => invalidate(),
  });
}

/** Generic child-record mutation (persons / items / sections / diary). */
export function useCaseChildMutation(caseId, fn) {
  const invalidate = useInvalidateCase();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => invalidate(caseId),
  });
}

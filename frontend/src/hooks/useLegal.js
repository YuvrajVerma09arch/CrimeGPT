import { useMutation, useQuery } from "@tanstack/react-query";
import { legalService } from "../services/legalService";

export function useSuggestSections() {
  return useMutation({
    mutationFn: ({ narrative, language }) =>
      legalService.suggest(narrative, language),
  });
}

export function useLegalSearch(q, act) {
  return useQuery({
    queryKey: ["legal", "search", q, act],
    queryFn: () => legalService.search(q, act),
    enabled: q.trim().length >= 2,
  });
}

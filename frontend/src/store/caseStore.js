import { create } from "zustand";

/** Draft state for the NewCase flow: analysis results survive tab switches. */
export const useCaseStore = create((set) => ({
  suggestions: null, // { sections, judgments, entities } from /legal/suggest
  acceptedSections: [], // sections the officer accepted for the new case

  setSuggestions: (suggestions) => set({ suggestions }),

  acceptSection: (section) =>
    set((s) => {
      const key = `${section.act}-${section.section}`;
      if (
        s.acceptedSections.some((x) => `${x.act}-${x.section}` === key)
      ) {
        return s;
      }
      return { acceptedSections: [...s.acceptedSections, section] };
    }),

  removeAcceptedSection: (index) =>
    set((s) => ({
      acceptedSections: s.acceptedSections.filter((_, i) => i !== index),
    })),

  resetDraft: () => set({ suggestions: null, acceptedSections: [] }),
}));

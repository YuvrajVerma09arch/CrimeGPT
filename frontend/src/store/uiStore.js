import { create } from "zustand";

let toastSeq = 0;

export const useUiStore = create((set, get) => ({
  toasts: [],

  pushToast: (type, message, timeout = 4000) => {
    const id = ++toastSeq;
    set((s) => ({ toasts: [...s.toasts, { id, type, message }] }));
    if (timeout > 0) {
      setTimeout(() => get().dismissToast(id), timeout);
    }
    return id;
  },

  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export function toast(type, message) {
  return useUiStore.getState().pushToast(type, message);
}

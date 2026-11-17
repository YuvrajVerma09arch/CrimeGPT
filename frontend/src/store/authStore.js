import { create } from "zustand";
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from "../services/api";

export const useAuthStore = create((set) => ({
  user: null,
  initialized: false,

  setAuth: ({ access_token, refresh_token, user }) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
    set({ user, initialized: true });
  },

  setUser: (user) => set({ user, initialized: true }),

  logout: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    set({ user: null, initialized: true });
  },
}));

export function hasStoredToken() {
  return Boolean(localStorage.getItem(ACCESS_TOKEN_KEY));
}

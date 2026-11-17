import { useCallback, useEffect, useState } from "react";
import { authService } from "../services/authService";
import { useAuthStore, hasStoredToken } from "../store/authStore";

export function useAuth() {
  const { user, initialized, setAuth, setUser, logout } = useAuthStore();

  const login = useCallback(
    async (badgeNo, password) => {
      const data = await authService.login(badgeNo, password);
      setAuth(data);
      return data.user;
    },
    [setAuth]
  );

  const signOut = useCallback(async () => {
    await authService.logout();
    logout();
  }, [logout]);

  return { user, initialized, login, signOut };
}

/** Loads /auth/me once when a token exists but the store is empty. */
export function useLoadUser() {
  const { user, setUser, logout } = useAuthStore();
  const [loading, setLoading] = useState(!user && hasStoredToken());

  useEffect(() => {
    let cancelled = false;
    if (!user && hasStoredToken()) {
      authService
        .me()
        .then((me) => {
          if (!cancelled) setUser(me);
        })
        .catch(() => {
          if (!cancelled) logout();
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    } else {
      setLoading(false);
    }
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { user, loading, authenticated: hasStoredToken() };
}

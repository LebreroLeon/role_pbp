import { useEffect } from "react";

import { api } from "../../api/client";
import { useAuthStore } from "../../stores/authStore";

/** Rehydrate user profile from GET /auth/me when a persisted token exists. */
export function AuthBootstrap() {
  const token = useAuthStore((state) => state.token);
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    api
      .me()
      .then((user) => {
        if (!cancelled) setAuth(token, user);
      })
      .catch(() => {
        if (!cancelled) clearAuth();
      });

    return () => {
      cancelled = true;
    };
  }, [token, setAuth, clearAuth]);

  return null;
}

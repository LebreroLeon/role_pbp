import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api, type LoginPayload, type RegisterPayload } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { useAuthStore } from "../../stores/authStore";

export function useLoginMutation() {
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (payload: LoginPayload) => api.login(payload),
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
      navigate("/campaigns");
    },
  });
}

export function useRegisterMutation() {
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (payload: RegisterPayload) => api.register(payload),
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
      navigate("/campaigns");
    },
  });
}

export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const navigate = useNavigate();

  return () => {
    clearAuth();
    navigate("/login");
  };
}

export function useUpdateDisplayNameMutation() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.token);
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: (displayName: string) => api.updateMe(displayName),
    onSuccess: (user) => {
      if (token) {
        setAuth(token, user);
      }
      queryClient.setQueryData(queryKeys.auth.me, user);
      queryClient.invalidateQueries({
        predicate: (query) =>
          Array.isArray(query.queryKey) &&
          query.queryKey[0] === "campaigns" &&
          query.queryKey[2] === "members",
      });
    },
  });
}

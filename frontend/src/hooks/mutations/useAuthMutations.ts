import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api, type LoginPayload, type RegisterPayload } from "../../api/client";
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

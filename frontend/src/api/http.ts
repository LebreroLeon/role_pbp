import { useAuthStore } from "../stores/authStore";
import { getApiBase } from "./apiBase";

const API_BASE = getApiBase();

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const token = useAuthStore.getState().token;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(init?.headers ?? {}),
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!response.ok) {
    const text = await response.text();
    let message = text || `Request failed: ${response.status}`;
    if (response.status === 405 && !API_BASE) {
      message =
        "Request failed: 405 — el frontend no tiene VITE_API_URL en el build. " +
        "En Vercel: Settings → Environment Variables → Production → VITE_API_URL=https://rolepbp-api.onrender.com y Redeploy. " +
        "Luego recarga forzada (Ctrl+Shift+R) o ventana de incógnito.";
    }
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (typeof json.detail === "string") {
        message = json.detail;
      }
    } catch {
      // keep raw text
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function httpUpload<T>(
  path: string,
  formData: FormData,
  init?: Omit<RequestInit, "body" | "headers">,
): Promise<T> {
  const token = useAuthStore.getState().token;
  const headers: HeadersInit = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, method: "POST", headers, body: formData });

  if (!response.ok) {
    const text = await response.text();
    let message = text || `Request failed: ${response.status}`;
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (typeof json.detail === "string") message = json.detail;
    } catch {
      // keep raw text
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

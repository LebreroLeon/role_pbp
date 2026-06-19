import { useAuthStore } from "../stores/authStore";
import { ApiError } from "./http";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export async function downloadAuthenticatedFile(path: string, filename: string): Promise<void> {
  const token = useAuthStore.getState().token;
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { headers });
  if (!response.ok) {
    throw new ApiError(`Download failed: ${response.status}`, response.status);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function fetchAuthenticatedBlob(path: string): Promise<Blob> {
  const token = useAuthStore.getState().token;
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { headers });
  if (!response.ok) {
    throw new ApiError(`Request failed: ${response.status}`, response.status);
  }

  return response.blob();
}

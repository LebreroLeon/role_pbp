const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function getApiBase(): string {
  return API_BASE;
}

export function buildApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

/** WebSocket URL: uses VITE_API_URL when set (Vercel + Render), else same-origin. */
export function buildWsUrl(path: string, params?: URLSearchParams): string {
  const query = params ? `?${params.toString()}` : "";

  if (API_BASE) {
    const apiUrl = new URL(API_BASE);
    const protocol = apiUrl.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${apiUrl.host}${path}${query}`;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${path}${query}`;
}

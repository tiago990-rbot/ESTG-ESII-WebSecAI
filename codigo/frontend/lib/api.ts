import type { ScanComparison, ScanDetail, ScanListItem, ScanStats, User } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "websec_token";
const AUTH_EVENT = "websec-auth-changed";

export function notifyAuthChanged() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_EVENT));
  }
}

export function onAuthChanged(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(AUTH_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(AUTH_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function isLoggedIn() {
  return Boolean(getToken());
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  notifyAuthChanged();
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  notifyAuthChanged();
}

export async function request<T>(path: string, options: RequestInit = {}, authenticated = true): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  const token = authenticated ? getToken() : null;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    if (response.status === 401 && token) clearToken();
    let message = `Erro ${response.status}`;
    try {
      const data = await response.json();
      message = Array.isArray(data.detail) ? data.detail.map((item: { msg?: string }) => item.msg || "Dados inválidos").join("; ") : data.detail || message;
    } catch {}
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  changePassword: (payload: { current_password: string; new_password: string; confirmation: string }) =>
    request<void>("/api/v1/auth/password/change", { method: "POST", body: JSON.stringify(payload), cache: "no-store" }),

  resetPassword: (payload: { token: string; new_password: string; confirmation: string }) =>
    request<void>("/api/v1/auth/password/reset", { method: "POST", body: JSON.stringify(payload), cache: "no-store" }, false),

  authConfiguration: (signal?: AbortSignal) =>
    request<{ public_registration_enabled: boolean }>("/api/v1/auth/configuration", { signal }),

  register: (payload: { username: string; email: string; password: string }) =>
    request<User>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(payload) }),

  login: (payload: { username_or_email: string; password: string }) =>
    request<{ access_token: string; token_type: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  me: () => request<User>("/api/v1/users/me"),

  createScan: (url: string, authorized: boolean) =>
    request<{ message: string; scan_id: number }>("/api/v1/scans/", { method: "POST", body: JSON.stringify({ url, authorized }) }),

  listScans: () => request<ScanListItem[]>("/api/v1/scans/"),

  getScan: (id: string | number) => request<ScanDetail>(`/api/v1/scans/${id}`),

  stats: () => request<ScanStats>("/api/v1/scans/stats/overview"),

  comparison: (id: string | number) => request<ScanComparison>(`/api/v1/scans/${id}/comparison`),
};

export async function downloadReport(scanId: number | string) {
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}/api/v1/scans/${scanId}/report`, { headers });
  if (!response.ok) throw new Error("Não foi possível gerar o PDF");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `websec-check-${scanId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// Thin API client for the Порядок backend. Token + base live in localStorage so
// the app works from any host (set them on the login screen).
import type { Bundle, Touch } from "./types";

const API_KEY = "poryadok.api";
const TOKEN_KEY = "poryadok.token";
const DEFAULT_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8000";

export function apiBase(): string {
  return (localStorage.getItem(API_KEY) || DEFAULT_BASE).replace(/\/+$/, "");
}
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setSession(base: string, token: string): void {
  localStorage.setItem(API_KEY, base.replace(/\/+$/, ""));
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

class AuthError extends Error {}

async function authed(path: string, init: RequestInit = {}): Promise<Response> {
  const resp = await fetch(apiBase() + path, {
    ...init,
    headers: { ...(init.headers || {}), Authorization: `Bearer ${getToken() ?? ""}` },
  });
  if (resp.status === 401) {
    clearToken();
    throw new AuthError("Сессия истекла");
  }
  return resp;
}

export async function login(email: string, password: string, base: string): Promise<string> {
  const resp = await fetch(base.replace(/\/+$/, "") + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail || "Не удалось войти");
  }
  return ((await resp.json()) as { access_token: string }).access_token;
}

export async function getState(): Promise<Bundle> {
  return (await authed("/state")).json();
}
export async function putState(bundle: Bundle): Promise<Bundle> {
  return (
    await authed("/state", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bundle),
    })
  ).json();
}
export async function getTouches(): Promise<Touch[]> {
  return (await authed("/suggestions/touches")).json();
}

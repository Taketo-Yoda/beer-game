import type { DebriefView, GameStateView, Role } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export function createGame(humanRole: Role): Promise<GameStateView> {
  return request("/api/games", {
    method: "POST",
    body: JSON.stringify({ human_role: humanRole }),
  });
}

export function getGame(gameId: string): Promise<GameStateView> {
  return request(`/api/games/${gameId}`);
}

export function submitOrder(gameId: string, order: number): Promise<GameStateView> {
  return request(`/api/games/${gameId}/orders`, {
    method: "POST",
    body: JSON.stringify({ order }),
  });
}

export function getDebrief(gameId: string): Promise<DebriefView> {
  return request(`/api/games/${gameId}/debrief`);
}

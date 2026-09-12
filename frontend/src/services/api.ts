/**
 * API service — thin wrapper around fetch for communicating with the FastAPI backend.
 *
 * The base URL is read from the VITE_API_BASE_URL environment variable so it
 * never needs to be hardcoded.  In development the Vite proxy rewrites /api/*
 * to http://localhost:8000/*, so VITE_API_BASE_URL can be left empty.
 */
import type { HealthResponse, RootResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

/**
 * Generic fetch wrapper that returns the parsed JSON body or throws on
 * non-2xx responses / network errors.
 */
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

// ── Typed endpoint helpers ────────────────────────────────────────────────

export const apiService = {
  /** GET / */
  getRoot: (): Promise<RootResponse> => apiFetch<RootResponse>('/'),

  /** GET /health */
  getHealth: (): Promise<HealthResponse> => apiFetch<HealthResponse>('/health'),
};

export default apiService;

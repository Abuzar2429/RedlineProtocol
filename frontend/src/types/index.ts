/**
 * Shared TypeScript types for the AI Governance Crisis Simulator.
 * Phase 1: only API/health types.
 * Simulation types (Country, Scenario, Decision, etc.) will be added in Phase 2+.
 */

/** Response from GET / */
export interface RootResponse {
  message: string;
}

/** Response from GET /health */
export interface HealthResponse {
  status: string;
}

/** Frontend-side connection status */
export type ConnectionStatus = 'checking' | 'connected' | 'offline';

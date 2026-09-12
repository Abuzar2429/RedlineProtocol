/**
 * Authoritative REST API Client for Phase 8 endpoints.
 */
import type {
  ApiErrorResponse,
  CountryData,
  CountryState,
  CreateSimulationRequest,
  CreateSimulationResponse,
  FullSimulationStateResponse,
  HealthResponse,
  RAGHealthResponse,
  ScenarioData,
  ScoringResult,
  SimulationEvent,
  SimulationStepResponse,
  SimulationSummary,
} from '../../types';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    // In dev, Vite proxy maps /api -> http://localhost:8000/api
    this.baseUrl = baseUrl ?? (import.meta.env.VITE_API_BASE_URL ?? '');
  }

  private async request<T>(
    path: string,
    options: RequestInit = {},
    timeoutMs: number = 30000
  ): Promise<T> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);

    const url = `${this.baseUrl}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    };

    try {
      const res = await fetch(url, {
        method: options.method ?? 'GET',
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!res.ok) {
        let detail = res.statusText;
        try {
          const errData = (await res.json()) as ApiErrorResponse;
          if (errData?.detail) detail = errData.detail;
        } catch {
          // ignore non-json error responses
        }
        throw new ApiError(res.status, detail);
      }

      return (await res.json()) as T;
    } catch (err: unknown) {
      if (err instanceof ApiError) throw err;
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new ApiError(408, `Request timed out after ${timeoutMs}ms`);
      }
      const message = err instanceof Error ? err.message : 'Network request failed';
      throw new ApiError(0, message);
    } finally {
      clearTimeout(id);
    }
  }

  // ── Health Check ───────────────────────────────────────────────────────────
  getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // ── Scenarios ──────────────────────────────────────────────────────────────
  getScenarios(): Promise<ScenarioData[]> {
    return this.request<ScenarioData[]>('/api/scenarios');
  }

  getScenario(id: string): Promise<ScenarioData> {
    return this.request<ScenarioData>(`/api/scenarios/${id}`);
  }

  // ── Countries ──────────────────────────────────────────────────────────────
  getCountries(): Promise<CountryData[]> {
    return this.request<CountryData[]>('/api/countries');
  }

  getCountry(id: string): Promise<CountryData> {
    return this.request<CountryData>(`/api/countries/${id}`);
  }

  // ── Simulations ────────────────────────────────────────────────────────────
  createSimulation(data: CreateSimulationRequest): Promise<CreateSimulationResponse> {
    return this.request<CreateSimulationResponse>('/api/simulations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  listSimulations(): Promise<SimulationSummary[]> {
    return this.request<SimulationSummary[]>('/api/simulations');
  }

  getSimulation(id: string): Promise<FullSimulationStateResponse> {
    return this.request<FullSimulationStateResponse>(`/api/simulations/${id}`);
  }

  getFullSimulationState(id: string): Promise<FullSimulationStateResponse> {
    return this.getSimulation(id);
  }

  // ── Simulation Controls ────────────────────────────────────────────────────
  startSimulation(id: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/api/simulations/${id}/start`, {
      method: 'POST',
    });
  }

  stepSimulation(id: string): Promise<SimulationStepResponse> {
    return this.request<SimulationStepResponse>(`/api/simulations/${id}/step`, {
      method: 'POST',
    });
  }

  runSimulation(id: string, maxTicks?: number): Promise<{ message: string }> {
    const q = maxTicks ? `?max_ticks=${maxTicks}` : '';
    return this.request<{ message: string }>(`/api/simulations/${id}/run${q}`, {
      method: 'POST',
    });
  }

  pauseSimulation(id: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/api/simulations/${id}/pause`, {
      method: 'POST',
    });
  }

  resumeSimulation(id: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/api/simulations/${id}/resume`, {
      method: 'POST',
    });
  }

  stopSimulation(id: string): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(`/api/simulations/${id}/stop`, {
      method: 'POST',
    });
  }

  // ── Country Inspection & Events ────────────────────────────────────────────
  getSimulationCountries(id: string): Promise<CountryState[]> {
    return this.request<CountryState[]>(`/api/simulations/${id}/countries`);
  }

  getSimulationEvents(
    id: string,
    params?: {
      event_type?: string;
      country_id?: string;
      start_tick?: number;
      end_tick?: number;
    }
  ): Promise<SimulationEvent[]> {
    const q = new URLSearchParams();
    if (params?.event_type) q.set('event_type', params.event_type);
    if (params?.country_id) q.set('country_id', params.country_id);
    if (params?.start_tick !== undefined) q.set('start_tick', String(params.start_tick));
    if (params?.end_tick !== undefined) q.set('end_tick', String(params.end_tick));
    const qs = q.toString() ? `?${q.toString()}` : '';
    return this.request<SimulationEvent[]>(`/api/simulations/${id}/events${qs}`);
  }

  // ── Scoring ────────────────────────────────────────────────────────────────
  calculateScore(id: string, recalculate = false): Promise<ScoringResult> {
    const q = recalculate ? '?recalculate=true' : '';
    return this.request<ScoringResult>(`/api/simulations/${id}/score${q}`, {
      method: 'POST',
    });
  }

  getScore(id: string): Promise<ScoringResult> {
    return this.request<ScoringResult>(`/api/simulations/${id}/score`);
  }

  // ── RAG ────────────────────────────────────────────────────────────────────
  getRAGHealth(): Promise<RAGHealthResponse> {
    return this.request<RAGHealthResponse>('/api/rag/health');
  }
}

export const apiClient = new ApiClient();
export default apiClient;

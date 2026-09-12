/**
 * REST API request and response DTOs matching backend endpoints.
 */
import type {
  CoordinatorProposal,
  CountryState,
  DecisionRecord,
  SimulationEvent,
  SimulationMode,
  SimulationStatus,
} from './simulation';
export type { ScoringResult, SimulationSummary } from './simulation';

export interface RootResponse {
  message: string;
}

export interface HealthResponse {
  status: string;
}

export interface ScenarioAction {
  id: string;
  label: string;
  description: string;
  risk_reduction_value: number;
  coordination_effect: number;
  requires_agreement: boolean;
  visibility: string;
}

export interface ScenarioData {
  id: string;
  title: string;
  description: string;
  severity: number;
  affected_countries: string[];
  initial_detection: string;
  information_delay: Record<string, number>;
  available_actions: ScenarioAction[];
  timeline?: Array<{
    tick: number;
    title: string;
    description: string;
    event_type: string;
  }>;
}

export interface CountryData {
  id: string;
  name: string;
  code: string;
  flag?: string;
  region: string;
  geopolitical_bloc?: string;
  strategic_priorities: string[];
  risk_tolerance: string;
  coordination_willingness: number;
  ai_capability_level: string;
  ai_policy_position: string;
  allies: string[];
  rivals: string[];
}

export interface CreateSimulationRequest {
  scenario_id: string;
  mode?: SimulationMode;
}

export interface CreateSimulationResponse {
  simulation_id: string;
  scenario_id: string;
  mode: SimulationMode;
  status: SimulationStatus;
  current_tick: number;
  current_time: string;
  message: string;
}

export interface SimulationStepResponse {
  simulation_id: string;
  status: SimulationStatus;
  current_tick: number;
  current_time: string;
  processed_events_count: number;
  events: SimulationEvent[];
  is_completed: boolean;
}

export interface FullSimulationStateResponse {
  simulation_id: string;
  scenario_id: string;
  mode: SimulationMode;
  status: SimulationStatus;
  current_tick: number;
  current_time: string;
  crisis_state: {
    crisis_id: string;
    title: string;
    severity: number;
    phase: string;
    escalation_level: number;
    resolved: boolean;
  };
  countries: Record<string, CountryState>;
  decisions: DecisionRecord[];
  active_events: SimulationEvent[];
  event_history: SimulationEvent[];
  proposals: CoordinatorProposal[];
  negotiations: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
}

export interface RAGHealthResponse {
  status: string;
  rag_enabled: boolean;
  collection_name: string;
  document_count: number;
  chunk_count: number;
  embedding_provider: string;
  embedding_model: string;
  embedding_dimension: number;
  last_ingestion_time: string | null;
}

export interface ApiErrorResponse {
  detail: string;
  status?: number;
}

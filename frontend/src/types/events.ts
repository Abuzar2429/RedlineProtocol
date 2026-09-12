/**
 * WebSocket event models matching backend Phase 8 schemas.
 */
import type {
  CoordinatorProposal,
  CountryState,
  ScoringResult,
  SimulationEvent,
  SimulationMode,
  SimulationStatus,
} from './simulation';

export type WebSocketEventType =
  | 'SNAPSHOT'
  | 'SIMULATION_STARTED'
  | 'STEP_COMPLETED'
  | 'SIMULATION_PAUSED'
  | 'SIMULATION_RESUMED'
  | 'SIMULATION_STOPPED'
  | 'SIMULATION_COMPLETED'
  | 'CRISIS_EVENT_TRIGGERED'
  | 'COUNTRY_STATUS_CHANGED'
  | 'DECISION_RECORDED'
  | 'COORDINATOR_PROPOSAL'
  | 'NEGOTIATION_STARTED'
  | 'NEGOTIATION_ROUND_COMPLETED'
  | 'NEGOTIATION_OUTCOME'
  | 'SCORING_COMPLETED'
  | 'tick_advanced'
  | 'step_completed'
  | 'simulation_started'
  | 'simulation_paused'
  | 'simulation_resumed'
  | 'simulation_stopped'
  | 'simulation_completed'
  | 'simulation_status_changed'
  | 'country_status_changed'
  | 'decision_recorded'
  | 'coordinator_proposal'
  | 'state_snapshot'
  | 'event'
  | 'decision'
  | 'negotiation'
  | 'metrics'
  | 'complete'
  | 'error'
  | 'pong'
  | (string & {});

export type WebSocketCategory =
  | 'system'
  | 'simulation'
  | 'crisis'
  | 'country'
  | 'negotiation'
  | 'scoring'
  | (string & {});

export interface WebSocketEventEnvelope<T = Record<string, unknown>> {
  event_id?: string;
  event_type: WebSocketEventType;
  simulation_id: string;
  tick: number;
  timestamp: string;
  category?: WebSocketCategory;
  payload: T;
  emitted_at?: string;
}

export interface SimulationSnapshotPayload {
  simulation_id: string;
  status: SimulationStatus;
  mode: SimulationMode;
  scenario_id: string;
  crisis_id: string;
  title: string;
  severity: number;
  tick: number;
  timestamp: string;
  countries: CountryState[];
  recent_events: SimulationEvent[];
  proposals: CoordinatorProposal[];
  negotiations: Array<Record<string, unknown>>;
  scoring_summary?: ScoringResult | null;
}

export interface WebSocketClientMessage {
  action: 'ping' | 'step' | 'pause' | 'resume' | 'start' | 'get_snapshot';
  payload?: Record<string, unknown>;
}

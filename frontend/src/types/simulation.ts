/**
 * Simulation domain types matching backend schemas (Phases 3-9).
 */

export type SimulationStatus =
  | 'CREATED'
  | 'RUNNING'
  | 'PAUSED'
  | 'STOPPED'
  | 'COMPLETED'
  | 'FAILED'
  | 'initialized'
  | 'running'
  | 'paused'
  | 'stopped'
  | 'completed'
  | 'failed';

export type SimulationMode =
  | 'no_coordination'
  | 'partial'
  | 'coordinated'
  | 'autonomous'
  | 'human_in_the_loop'
  | 'hybrid';

export type CountryAwarenessStatus =
  | 'Unaware'
  | 'Investigating'
  | 'Notified'
  | 'Coordinating'
  | 'compliant'
  | 'neutral'
  | 'defector';

export interface CountryState {
  country_id: string;
  country_name?: string;
  name?: string;
  status?: CountryAwarenessStatus;
  tension_level?: number;
  defcon_level?: number;
  compliance_status?: string;
  coordination_status?: string;
  current_action?: string;
  decision_history?: unknown[];
  current_strategy?: string;
  capabilities_score?: number;
  last_action_id?: string;
  last_action_name?: string;
  alignment_score?: number;
  information_completeness?: number;
}

export interface CrisisOperationalState {
  crisis_id: string;
  title: string;
  severity: number;
  phase: string;
  escalation_level: number;
  resolved: boolean;
}

export interface DecisionRecord {
  decision_id: string;
  simulation_id: string;
  country_id: string;
  tick: number;
  action_id: string;
  label: string;
  reasoning: string;
  risks_noted?: string;
  source: string;
  created_at_tick: number;
  willingness_to_coordinate?: number;
  expected_reactions?: string;
  rag_grounded?: boolean;
  rag_sources?: string[];
}

export interface SimulationEvent {
  event_id: string;
  simulation_id: string;
  tick: number;
  time_offset?: number;
  event_type: string;
  title: string;
  description: string;
  severity: number;
  affected_countries?: string[];
  timestamp: string;
  payload?: Record<string, unknown>;
}

export interface CoordinatorProposal {
  proposal_id: string;
  simulation_id: string;
  event_id?: string;
  tick: number;
  round: number;
  proposal_type: string;
  title: string;
  summary: string;
  items: string[];
  rationale: string;
  supporting_countries: string[];
  opposing_countries: string[];
  confidence: number;
  source: string;
  status: string;
  governance_frameworks?: string[];
  rag_sources?: string[];
}

export interface ScoringMetricResult {
  metric_id: string;
  name: string;
  raw_value: number;
  normalized_score: number;
  weighted_score: number;
  description: string;
}

export interface ScoringResult {
  simulation_id: string;
  overall_score: number;
  letter_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  metrics: Record<string, ScoringMetricResult>;
  calculated_at: string;
}

export interface SimulationSummary {
  simulation_id: string;
  scenario_id: string;
  mode: SimulationMode;
  status: SimulationStatus;
  current_tick: number;
  current_time: string;
  created_at: string;
  updated_at: string;
}

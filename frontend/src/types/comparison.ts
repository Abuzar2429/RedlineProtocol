import type { SimulationMode, SimulationStatus, SimulationMetrics, MetricResult } from './simulation';
import type { NegotiationOutcome } from './simulation';

export type ComparisonStatus =
  | 'CREATED'
  | 'INITIALIZING'
  | 'RUNNING'
  | 'COLLECTING_RESULTS'
  | 'COMPLETED'
  | 'FAILED';

export type ComparisonWinner =
  | 'no_coordination'
  | 'partial'
  | 'coordinated'
  | 'TIE'
  | 'INCOMPLETE'
  | 'FAILED';

export interface CreateComparisonRequest {
  scenario_id: string;
  max_ticks?: number;
  metadata?: Record<string, unknown>;
}

export interface ModeComparisonResult {
  mode: SimulationMode;
  mode_name: string;
  simulation_id: string;
  status: SimulationStatus;
  final_tick: number;
  overall_score?: number | null;
  score_grade?: string | null;
  performance_headline?: string | null;
  is_winner: boolean;
  scoring_result?: unknown;
  metrics?: SimulationMetrics | null;
  metric_breakdown: MetricResult[];
  negotiation_outcome?: NegotiationOutcome | null;
  events_count: number;
  decisions_count: number;
  error?: string | null;
}

export interface ComparisonDelta {
  baseline_mode: SimulationMode;
  compared_mode: SimulationMode;
  overall_score_delta: number;
  risk_reduction_delta_pct: number;
  response_time_delta_min: number;
  coordination_ratio_delta: number;
  unresolved_issues_delta: number;
  final_tick_delta: number;
}

export interface ComparisonRun {
  comparison_id: string;
  scenario_id: string;
  scenario_title: string;
  status: ComparisonStatus;
  created_at: string;
  completed_at?: string | null;
  modes_evaluated: SimulationMode[];
  results: Record<string, ModeComparisonResult>;
  winner?: ComparisonWinner | null;
  winner_reason?: string | null;
  summary_headline: string;
  summary_narrative: string;
  deltas: ComparisonDelta[];
  is_authoritative: boolean;
  metadata: Record<string, unknown>;
}

import type { ComparisonRun } from './comparison';

export type ExecutionMode = 'LIVE' | 'DEMO' | 'REPLAY';

export interface DemoLaunchRequest {
  scenario_id?: string;
  seed?: number;
  max_ticks?: number;
  metadata?: Record<string, unknown>;
}

export interface DemoRun {
  demo_id: string;
  scenario_id: string;
  scenario_title: string;
  seed: number;
  execution_mode: 'DEMO';
  status: string;
  comparison_id: string;
  comparison?: ComparisonRun | null;
  created_at: string;
  completed_at?: string | null;
  is_deterministic: boolean;
  fallback_active: boolean;
  metadata: Record<string, unknown>;
}

export interface ReplayEvent {
  sequence_number: number;
  tick: number;
  timestamp: string;
  event_type: string;
  source: string;
  description: string;
  affected_countries: string[];
  payload: Record<string, unknown>;
  mode?: string;
}

export interface ReplaySession {
  replay_id: string;
  source_type: 'simulation' | 'comparison';
  source_id: string;
  scenario_id: string;
  scenario_title: string;
  seed?: number | null;
  execution_mode: 'REPLAY';
  created_at: string;
  total_ticks: number;
  total_events: number;
  events: ReplayEvent[];
  scoring_result?: Record<string, unknown> | null;
  comparison_result?: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
}

export interface ReplayStateSnapshot {
  replay_id: string;
  current_tick: number;
  current_time: string;
  events_played: number;
  total_events: number;
  is_completed: boolean;
  visible_events: ReplayEvent[];
}

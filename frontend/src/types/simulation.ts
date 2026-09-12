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
  unresolved_issues?: string[];
  confidence: number;
  source: string;
  status: string;
  governance_frameworks?: string[];
  rag_sources?: string[];
}

export type MetricId = 'risk_reduction' | 'response_time' | 'coordination' | 'unresolved_issues';
export type ScoreGrade = 'A' | 'B' | 'C' | 'D' | 'F';

export interface MetricResult {
  metric_id: MetricId;
  name: string;
  raw_value: number;
  unit: string;
  display_value: string;
  normalized_score: number;
  weight: number;
  weighted_score: number;
  interpretation: string;
  evidence?: Record<string, unknown>;
}

export interface SimulationMetrics {
  risk_initial?: number;
  risk_final?: number;
  risk_reduction_pct?: number;
  response_time_minutes?: number;
  coordination_ratio?: number;
  countries_coordinating?: number;
  countries_total?: number;
  unresolved_issues?: string[];
  unresolved_issues_count?: number;
  negotiation_rounds?: number;
  agreement_reached?: boolean;
  simulation_mode?: SimulationMode;
  current_risk?: number;
}

export interface ScoringResult {
  scoring_id?: string;
  simulation_id: string;
  scenario_id?: string;
  simulation_mode?: SimulationMode;
  formula_version?: string;
  overall_score: number;
  score_grade?: ScoreGrade;
  letter_grade?: ScoreGrade;
  performance_headline?: string;
  simulation_status?: string;
  calculated_at_tick?: number;
  metrics?: SimulationMetrics | Record<string, unknown>;
  metric_breakdown?: MetricResult[];
  is_authoritative?: boolean;
  calculated_at?: string;
}

// Backward-compatibility alias
export type ScoringMetricResult = MetricResult;

export type VoteType = 'Approve' | 'Reject' | 'Undecided';

export type NegotiationStatus =
  | 'PROPOSED'
  | 'NEGOTIATION_OPEN'
  | 'ROUND_ACTIVE'
  | 'POSITIONS_COLLECTED'
  | 'VOTING'
  | 'VOTE_EVALUATED'
  | 'REVISION_REQUIRED'
  | 'ACCEPTED'
  | 'PARTIAL_AGREEMENT'
  | 'FAILED'
  | 'BREAKDOWN'
  | 'MAX_ROUNDS_REACHED'
  | 'NO_QUORUM';

export interface Vote {
  vote_id: string;
  country_id: string;
  round: number;
  proposal_id: string;
  proposal_version: number;
  vote: VoteType;
  rationale: string;
  conditions_requested?: string[];
  objections_raised?: string[];
  created_at_tick?: number;
  created_at?: string;
}

export interface ProposalVersion {
  version: number;
  proposal_id: string;
  title: string;
  summary: string;
  items: string[];
  rationale: string;
  revision_reason?: string | null;
  unresolved_issues?: string[];
  created_at_tick?: number;
  source?: string;
  created_at?: string;
}

export interface VotingResult {
  round: number;
  proposal_version: number;
  coordination_mode?: SimulationMode;
  eligible_voters: number;
  votes_cast: number;
  votes_for: number;
  votes_against: number;
  abstentions: number;
  invalid_votes?: number;
  participation_rate: number;
  is_quorum_met: boolean;
  required_threshold: number;
  achieved_threshold: number;
  passed: boolean;
  status: 'PASSED' | 'FAILED' | 'NO_QUORUM' | 'TIE' | 'INSUFFICIENT_SUPPORT' | string;
  failure_reason?: string | null;
  approving_countries: string[];
  opposing_countries: string[];
  abstaining_countries: string[];
}

export interface NegotiationRound {
  round_number: number;
  proposal_version: ProposalVersion;
  votes?: Record<string, Vote>;
  voting_result?: VotingResult | null;
  unresolved_issues?: string[];
  status?: 'PENDING' | 'VOTING' | 'COMPLETED' | 'REVISION_REQUESTED' | string;
  started_at_tick?: number;
  completed_at_tick?: number | null;
}

export interface NegotiationOutcome {
  negotiation_id: string;
  simulation_id: string;
  coordination_mode?: SimulationMode;
  final_status:
    | 'ACCEPTED'
    | 'PARTIAL_AGREEMENT'
    | 'FAILED'
    | 'BREAKDOWN'
    | 'MAX_ROUNDS_REACHED'
    | 'NO_QUORUM'
    | string;
  agreement_reached: boolean;
  rounds_completed: number;
  final_proposal_version: number;
  final_proposal?: ProposalVersion | null;
  final_vote_result?: VotingResult | null;
  supporting_countries: string[];
  opposing_countries: string[];
  abstaining_countries: string[];
  unresolved_issues?: string[];
  failure_reason?: string | null;
  completed_at_tick?: number;
}

export interface NegotiationSession {
  negotiation_id: string;
  simulation_id: string;
  scenario_id?: string;
  coordination_mode?: SimulationMode;
  status: NegotiationStatus;
  current_round: number;
  max_rounds: number;
  participating_countries?: string[];
  proposal_versions?: ProposalVersion[];
  rounds?: NegotiationRound[];
  outcome?: NegotiationOutcome | null;
  created_at_tick?: number;
  created_at?: string;
  metadata?: Record<string, unknown>;
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


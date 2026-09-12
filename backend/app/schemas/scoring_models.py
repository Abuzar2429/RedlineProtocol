"""
Pydantic schemas for the Phase 7 Deterministic Scoring Engine:
- MetricResult: individual metric outcome, raw/normalized values, weight, evidence
- SimulationMetrics: exact spec-defined metrics object (Spec §6.5)
- ScoringInputSnapshot: immutable snapshot of simulation facts for reproducible scoring
- ScoringResult: complete evaluation bundle with overall score, grade, and metadata
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.simulation_models import SimulationMode


MetricId = Literal["risk_reduction", "response_time", "coordination", "unresolved_issues"]

ScoreGrade = Literal["A", "B", "C", "D", "F"]


class MetricResult(BaseModel):
    """
    Individual evaluation result for one of the four deterministic metrics.
    """
    metric_id: MetricId = Field(..., description="Unique metric identifier")
    name: str = Field(..., description="Human-readable metric name")
    raw_value: float = Field(..., description="Un-normalized raw value from simulation")
    unit: str = Field(..., description="Display unit (e.g. %, minutes, ratio, count)")
    display_value: str = Field(..., description="Formatted string for UI display (e.g. '14 min', '11/15', '↓63%')")
    normalized_score: float = Field(..., ge=0.0, le=100.0, description="Normalized score on 0-100 scale")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in overall composite score")
    weighted_score: float = Field(..., ge=0.0, le=100.0, description="Score contribution (normalized_score * weight)")
    interpretation: str = Field(..., description="Qualitative interpretation of metric performance")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Structured audit calculation evidence")


class SimulationMetrics(BaseModel):
    """
    Exact simulation metrics object matching Spec §6.5 and PRD §7.5.
    """
    risk_initial: float = Field(100.0, description="Baseline scenario risk")
    risk_final: float = Field(..., ge=0.0, le=100.0, description="Final estimated risk after actions & coordination")
    risk_reduction_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of risk eliminated")
    response_time_minutes: int = Field(..., ge=0, description="Virtual minutes from detection to coordinated response")
    coordination_ratio: float = Field(..., ge=0.0, le=1.0, description="Ratio of approving countries to total countries")
    countries_coordinating: int = Field(..., ge=0, description="Count of countries approving/coordinating")
    countries_total: int = Field(15, ge=1, description="Total eligible participating countries")
    unresolved_issues: List[str] = Field(default_factory=list, description="Distinct unresolved policy issues")
    unresolved_issues_count: int = Field(0, ge=0, description="Count of distinct unresolved issues")
    negotiation_rounds: int = Field(0, ge=0, description="Total negotiation rounds conducted")
    agreement_reached: bool = Field(False, description="Whether an agreement was ratified")
    simulation_mode: SimulationMode = Field("coordinated", description="Simulation coordination architecture")


class ScoringInputSnapshot(BaseModel):
    """
    Immutable snapshot of simulation state and negotiation facts used for deterministic scoring.
    Ensures identical inputs always produce bit-for-bit identical scores.
    """
    simulation_id: str = Field(..., description="Target simulation identifier")
    scenario_id: str = Field(..., description="Target scenario identifier")
    mode: SimulationMode = Field(..., description="Coordination mode used during run")
    start_tick: int = Field(0, ge=0, description="Initial detection tick offset")
    final_tick: int = Field(..., ge=0, description="Final simulation tick reached")
    simulation_status: str = Field(..., description="Simulation execution status (RUNNING, COMPLETED, etc.)")
    crisis_phase: str = Field(..., description="Final crisis operational phase")
    unique_actions_taken: List[str] = Field(default_factory=list, description="Deduplicated action IDs committed during run")
    action_risk_reductions: Dict[str, float] = Field(default_factory=dict, description="Deductions mapped per action")
    detection_tick: int = Field(0, ge=0, description="Tick when crisis was first detected")
    coordinated_action_tick: Optional[int] = Field(None, ge=0, description="Tick when coordinated response occurred")
    coordinated_action_occurred: bool = Field(False, description="Whether a coordinated action occurred")
    total_countries: int = Field(15, ge=1, description="Total eligible countries in scenario")
    participating_countries: List[str] = Field(default_factory=list, description="Country IDs participating in decisions")
    approving_countries: List[str] = Field(default_factory=list, description="Country IDs endorsing the response")
    opposing_countries: List[str] = Field(default_factory=list, description="Country IDs rejecting the response")
    undecided_countries: List[str] = Field(default_factory=list, description="Country IDs abstaining/undecided")
    negotiation_sessions_count: int = Field(0, ge=0, description="Total negotiation sessions held")
    negotiation_rounds_count: int = Field(0, ge=0, description="Total negotiation rounds across sessions")
    final_agreement_reached: bool = Field(False, description="Whether final negotiation agreement was achieved")
    final_negotiation_status: Optional[str] = Field(None, description="Terminal status of latest negotiation")
    unresolved_issues_raw: List[str] = Field(default_factory=list, description="Unfiltered candidate issues from negotiation")
    proposal_versions_count: int = Field(0, ge=0, description="Total proposal versions evaluated")
    initial_tick: int = Field(0, ge=0, description="Initial tick baseline")
    votes_count: int = Field(0, ge=0, description="Total votes cast across negotiation rounds")
    events_count: int = Field(0, ge=0, description="Total events recorded in event history")
    decisions_count: int = Field(0, ge=0, description="Total decisions made across countries")
    scenario_baseline_risk: float = Field(100.0, description="Baseline initial crisis risk")
    final_crisis_state: Optional[Dict[str, Any]] = Field(None, description="Snapshot of operational crisis state")
    country_states: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Snapshot of country states")
    negotiation_sessions: Optional[List[Dict[str, Any]]] = Field(None, description="Snapshot of negotiation sessions")
    final_negotiation_outcome: Optional[Dict[str, Any]] = Field(None, description="Snapshot of final negotiation outcome")
    proposal_versions: Optional[List[Dict[str, Any]]] = Field(None, description="Snapshot of proposal versions")
    votes: Optional[List[Dict[str, Any]]] = Field(None, description="Snapshot of votes cast")
    events: Optional[List[Dict[str, Any]]] = Field(None, description="Snapshot of timeline events")
    decisions: Optional[List[Dict[str, Any]]] = Field(None, description="Snapshot of country decision records")


class ScoringResult(BaseModel):
    """
    Comprehensive evaluation result produced by the Deterministic Scoring Engine.
    """
    scoring_id: str = Field(..., description="Unique scoring calculation identifier")
    simulation_id: str = Field(..., description="Associated simulation identifier")
    scenario_id: str = Field(..., description="Associated scenario identifier")
    simulation_mode: SimulationMode = Field(..., description="Coordination mode evaluated")
    formula_version: str = Field("1.0", description="Scoring formula specification version")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Composite weighted governance score (0-100)")
    score_grade: ScoreGrade = Field(..., description="Letter grade for governance performance")
    performance_headline: str = Field(..., description="One-line summary statement of the outcome")
    simulation_status: str = Field(..., description="Status of the simulation at scoring time")
    calculated_at_tick: int = Field(..., ge=0, description="Simulation tick at which score was calculated")
    metrics: SimulationMetrics = Field(..., description="Exact spec-defined metrics object")
    metric_breakdown: List[MetricResult] = Field(..., description="Detailed breakdown of each of the 4 metrics")
    input_snapshot: ScoringInputSnapshot = Field(..., description="Immutable snapshot of inputs used for calculation")
    mode_comparison_ready: bool = Field(True, description="Ready for multi-mode comparative runs (Phase 13)")
    is_authoritative: bool = Field(True, description="Calculated via code rules, zero LLM authority")

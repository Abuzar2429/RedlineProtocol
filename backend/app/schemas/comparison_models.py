"""
Pydantic schemas and domain models for the Phase 13 Three-Mode Comparison Engine.
Defines ComparisonRun, ModeComparisonResult, ComparisonDelta, and comparison lifecycle schemas.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.negotiation_models import NegotiationOutcome
from app.schemas.scoring_models import MetricResult, ScoringResult, SimulationMetrics
from app.schemas.simulation_models import SimulationMode, SimulationStatus


ComparisonStatus = Literal[
    "CREATED",
    "INITIALIZING",
    "RUNNING",
    "COLLECTING_RESULTS",
    "COMPLETED",
    "FAILED",
]

ComparisonWinner = Literal[
    "no_coordination",
    "partial",
    "coordinated",
    "TIE",
    "INCOMPLETE",
    "FAILED",
]


class CreateComparisonRequest(BaseModel):
    """
    Request payload to initiate a three-mode comparative run for a specific crisis scenario.
    """
    scenario_id: str = Field(..., description="Target crisis scenario identifier (e.g. 'scenario_01')")
    max_ticks: Optional[int] = Field(120, ge=10, le=240, description="Max tick boundary per simulation run")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional caller metadata or labels")


class ModeComparisonResult(BaseModel):
    """
    Structured outcome bundle for one of the three evaluated coordination modes.
    """
    mode: SimulationMode = Field(..., description="Evaluated coordination mode: no_coordination | partial | coordinated")
    mode_name: str = Field(..., description="Human-readable mode title")
    simulation_id: str = Field(..., description="Isolated simulation run ID")
    status: SimulationStatus = Field(..., description="Terminal simulation status: COMPLETED | FAILED")
    final_tick: int = Field(..., ge=0, description="Authoritative final simulation tick reached")
    overall_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Phase 7 composite score (0-100)")
    score_grade: Optional[str] = Field(None, description="Letter grade ('A' through 'F')")
    performance_headline: Optional[str] = Field(None, description="One-line outcome headline")
    is_winner: bool = Field(False, description="Whether this mode achieved the highest score")
    
    # Authoritative sub-results from Phases 6 & 7
    scoring_result: Optional[ScoringResult] = Field(None, description="Full Phase 7 deterministic scoring result")
    metrics: Optional[SimulationMetrics] = Field(None, description="Spec §6.5 SimulationMetrics object")
    metric_breakdown: List[MetricResult] = Field(default_factory=list, description="Exact 4 metric results")
    negotiation_outcome: Optional[NegotiationOutcome] = Field(None, description="Phase 6 negotiation outcome")
    
    # Audit & diagnostics
    events_count: int = Field(0, ge=0, description="Total events processed in this mode's run")
    decisions_count: int = Field(0, ge=0, description="Total policy decisions committed by nations")
    error: Optional[str] = Field(None, description="Diagnostic error if mode execution failed")


class ComparisonDelta(BaseModel):
    """
    Quantified variance between two coordination modes across key governance metrics.
    """
    baseline_mode: SimulationMode = Field(..., description="Reference baseline mode (e.g. 'no_coordination')")
    compared_mode: SimulationMode = Field(..., description="Target mode being compared (e.g. 'coordinated')")
    overall_score_delta: float = Field(..., description="compared.overall_score - baseline.overall_score")
    risk_reduction_delta_pct: float = Field(..., description="Variance in percentage of crisis risk eliminated")
    response_time_delta_min: int = Field(..., description="Minutes saved (negative = faster response)")
    coordination_ratio_delta: float = Field(..., description="Variance in multilateral consensus ratio")
    unresolved_issues_delta: int = Field(..., description="Variance in remaining deadlock issues")
    final_tick_delta: int = Field(..., description="Variance in total virtual duration ticks")


class ComparisonRun(BaseModel):
    """
    Complete, authoritative domain model representing a Three-Mode Comparative Run.
    Orchestrates execution of the SAME scenario across 'no_coordination', 'partial', and 'coordinated'.
    """
    comparison_id: str = Field(..., description="Unique comparison identifier (e.g. 'comp_01a2b3c4d5e6')")
    scenario_id: str = Field(..., description="Crisis scenario evaluated identically across all modes")
    scenario_title: str = Field(..., description="Human-readable crisis scenario title")
    status: ComparisonStatus = Field("CREATED", description="Lifecycle execution state")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp"
    )
    completed_at: Optional[str] = Field(None, description="ISO 8601 UTC completion timestamp")
    
    # Exact three modes guaranteed
    modes_evaluated: List[SimulationMode] = Field(
        default=["no_coordination", "partial", "coordinated"],
        description="Exact three coordination modes evaluated in this comparative run"
    )
    results: Dict[str, ModeComparisonResult] = Field(
        default_factory=dict,
        description="Map of mode ID ('no_coordination', 'partial', 'coordinated') to ModeComparisonResult"
    )
    
    # Deterministic Winner
    winner: Optional[ComparisonWinner] = Field(None, description="Deterministic winning mode or 'TIE'")
    winner_reason: Optional[str] = Field(None, description="Deterministic justification for winner determination")
    summary_headline: str = Field("", description="One-line synthesis of the comparison findings")
    summary_narrative: str = Field("", description="Detailed multi-paragraph deterministic comparison breakdown")
    
    # Deltas
    deltas: List[ComparisonDelta] = Field(default_factory=list, description="Computed metric variances between modes")
    
    # Audit & Provenance
    is_authoritative: bool = Field(True, description="Calculated via code rules, zero LLM authority")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata and runtime telemetry")

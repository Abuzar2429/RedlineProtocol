"""
Pydantic schemas for the Phase 3 Simulation Engine:
- Simulation State & Lifecycle
- Country Simulation State & Status transitions
- Virtual Event & Queue models
- Decision records
- Operational Crisis State
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.coordinator_models import CoordinatorProposal
from app.schemas.negotiation_models import NegotiationSession


# ── Status and Types ──────────────────────────────────────────────────────────

CountrySimulationStatus = Literal["Unaware", "Investigating", "Notified", "Coordinating"]

SimulationStatus = Literal["CREATED", "RUNNING", "PAUSED", "COMPLETED", "FAILED"]

SimulationMode = Literal["no_coordination", "partial", "coordinated"]

SimulationEventType = Literal[
    "CRISIS_TRIGGERED",
    "TIMELINE_EVENT",
    "INFORMATION_RECEIVED",
    "COUNTRY_NOTIFICATION",
    "DECISION_REQUIRED",
    "POLICY_ACTION",
    "COORDINATION_REQUEST",
    "NEGOTIATION_STARTED",
    "NEGOTIATION_ROUND_COMPLETED",
    "NEGOTIATION_PASSED",
    "NEGOTIATION_FAILED",
    "PROPOSAL_REVISION_REQUIRED",
    "CRISIS_ESCALATION",
    "CRISIS_DE_ESCALATION",
    "CRISIS_RESOLVED",
]


# ── State Models ──────────────────────────────────────────────────────────────

class CountrySimulationState(BaseModel):
    country_id: str = Field(..., description="Unique country identifier")
    name: str = Field(..., description="Country display name")
    status: CountrySimulationStatus = Field("Unaware", description="Sequential status progression")
    aware: bool = Field(False, description="Whether country is aware of the crisis")
    information_completeness: float = Field(0.0, ge=0.0, le=1.0, description="Completeness of received intelligence")
    current_action: Optional[str] = Field(None, description="Most recently committed policy action")
    coordination_status: Optional[str] = Field("Independent", description="Multilateral coordination alignment")
    decision_count: int = Field(0, description="Number of decisions taken in this simulation")
    last_updated_tick: int = Field(0, description="Tick at which state was last updated")


class CrisisOperationalState(BaseModel):
    scenario_id: str = Field(..., description="Scenario identifier")
    title: str = Field(..., description="Crisis scenario title")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity category")
    severity_score: float = Field(..., ge=0.0, le=1.0, description="Base severity fraction")
    current_risk: float = Field(100.0, description="Operational crisis risk score (starts at 100.0)")
    phase: str = Field("DETECTION", description="Current crisis operational phase")
    origin_country: str = Field(..., description="Originating state identifier")
    affected_countries: List[str] = Field(default_factory=list, description="IDs of affected states")
    impact_domains: List[str] = Field(default_factory=list, description="Domains impacted")


class SimulationEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    tick: int = Field(..., ge=0, description="Tick at which event occurs")
    priority: int = Field(10, description="Ordering priority (lower number = higher priority)")
    event_type: SimulationEventType = Field(..., description="Event categorization")
    source: str = Field("system", description="Event originator (system, scenario, country_id)")
    affected_countries: List[str] = Field(default_factory=list, description="Targeted or affected country IDs")
    description: str = Field(..., description="Human-readable event narrative")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured event payload")


class DecisionRecord(BaseModel):
    decision_id: str = Field(..., description="Unique decision identifier")
    simulation_id: str = Field(..., description="Associated simulation identifier")
    country_id: str = Field(..., description="Deciding country identifier")
    tick: int = Field(..., ge=0, description="Simulation tick when decision was recorded")
    action_id: str = Field(..., description="Selected action ID from scenario")
    label: str = Field(..., description="Action display label")
    reasoning: str = Field(..., description="Rationale justification")
    risks_noted: str = Field("", description="Anticipated risks noted in decision")
    source: str = Field("deterministic_placeholder", description="Decision engine source ('llm_agent' | 'deterministic_fallback' | 'deterministic_placeholder')")
    created_at_tick: int = Field(0, description="Tick when decision was scheduled")

    # LLM provenance & metadata (Phase 4+)
    provider: Optional[str] = Field(None, description="LLM provider name (e.g. anthropic, mock)")
    model: Optional[str] = Field(None, description="Model identifier used for inference")
    latency_ms: Optional[float] = Field(None, description="Inference latency in milliseconds")
    willingness_to_coordinate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Expressed coordination willingness")
    expected_reactions: Optional[str] = Field(None, description="Anticipated diplomatic reactions")
    prompt_version: Optional[str] = Field(None, description="Prompt version tag")

    # RAG provenance & citations (Phase 9)
    rag_grounded: bool = Field(False, description="Whether decision was grounded with RAG reference evidence")
    rag_sources: List[str] = Field(default_factory=list, description="Retrieved evidence citations or document IDs")


class SimulationState(BaseModel):
    simulation_id: str = Field(..., description="Unique UUID simulation identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    mode: SimulationMode = Field("coordinated", description="Simulation coordination architecture")
    status: SimulationStatus = Field("CREATED", description="Simulation execution status")
    current_tick: int = Field(0, ge=0, description="Current integer tick offset")
    current_time: str = Field("T+00", description="Formatted virtual simulation timestamp")
    crisis_state: CrisisOperationalState = Field(..., description="Operational crisis tracking state")
    countries: Dict[str, CountrySimulationState] = Field(..., description="Map of country simulation states")
    relationships: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Bilateral relationship scores")
    active_events: List[SimulationEvent] = Field(default_factory=list, description="Events processed in current tick")
    pending_decisions: List[Dict[str, Any]] = Field(default_factory=list, description="Decisions awaiting execution")
    decisions: List[DecisionRecord] = Field(default_factory=list, description="Recorded decision ledger")
    proposals: List[CoordinatorProposal] = Field(default_factory=list, description="International Coordinator proposals ledger")
    negotiations: List[NegotiationSession] = Field(default_factory=list, description="Negotiation sessions ledger")
    event_history: List[SimulationEvent] = Field(default_factory=list, description="Immutable full history log")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session configuration metadata")


# ── Request / Response DTOs ───────────────────────────────────────────────────

class CreateSimulationRequest(BaseModel):
    scenario_id: str = Field(..., description="ID of scenario to simulate (e.g. scenario_01)")
    mode: SimulationMode = Field("coordinated", description="Coordination mode")


class SimulationStepResponse(BaseModel):
    simulation_id: str
    status: SimulationStatus
    current_tick: int
    current_time: str
    processed_events_count: int
    events: List[SimulationEvent]
    is_completed: bool

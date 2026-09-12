"""
Pydantic schemas for the International Coordinator Agent (Phase 5).
Defines CoordinatorProposal, CoordinatorContext, and position summaries.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CountryPositionSummary(BaseModel):
    """
    Structured, shareable representation of a country's validated position.
    Strictly excludes internal LLM reasoning, chains-of-thought, or private state.
    """
    country_id: str = Field(..., description="Unique country ID")
    country_name: str = Field(..., description="Display name of fictional nation")
    status: str = Field(..., description="Awareness/operational state in simulation")
    action_id: str = Field(..., description="Validated action selected by the country")
    action_name: str = Field("", description="Human readable action title")
    willingness_to_coordinate: float = Field(0.5, ge=0.0, le=1.0, description="Expressed coordination willingness")
    risks_noted: List[str] = Field(default_factory=list, description="Public risks or concerns raised")
    conditions: List[str] = Field(default_factory=list, description="Conditions or stipulations for coordination")


class DeterministicAggregation(BaseModel):
    """
    Deterministic summary of country positions computed in code.
    The LLM is NOT used for vote counting or numerical aggregation.
    """
    total_countries: int = Field(..., description="Total participating nations")
    aware_countries: int = Field(..., description="Number of aware nations")
    action_counts: Dict[str, int] = Field(default_factory=dict, description="Count of nations per action ID")
    high_coordination_count: int = Field(0, description="Willingness >= 0.70")
    moderate_coordination_count: int = Field(0, description="0.40 <= Willingness < 0.70")
    low_coordination_count: int = Field(0, description="Willingness < 0.40")
    majority_action: Optional[str] = Field(None, description="Action selected by the most countries")


class PredictedVotes(BaseModel):
    """
    Predicted votes for the proposed international response.
    """
    approve: List[str] = Field(default_factory=list, description="Country IDs predicted to approve")
    oppose: List[str] = Field(default_factory=list, description="Country IDs predicted to oppose")
    abstain: List[str] = Field(default_factory=list, description="Country IDs predicted to abstain")


class CoordinatorProposal(BaseModel):
    """
    Strict, auditable schema for the International Coordinator's proposal.
    The Coordinator does NOT approve, reject, or execute this proposal.
    """
    proposal_id: str = Field(..., description="Unique proposal ID, e.g. prop_001_<uuid>")
    simulation_id: str = Field(..., description="Target simulation ID")
    event_id: str = Field("", description="Triggering event identifier")
    tick: int = Field(..., ge=0, description="Simulation tick when proposal was generated")
    round: int = Field(1, ge=1, description="Negotiation round index")
    proposal_type: str = Field(
        "JOINT_RESPONSE",
        description="Type of proposal: JOINT_RESPONSE | INFORMATION_SHARING | TECHNICAL_ASSISTANCE | INVESTIGATION_COMMISSION"
    )
    title: str = Field(..., description="Concise proposal title")
    summary: str = Field(..., description="High-level synthesis of common ground and proposed action")
    items: List[str] = Field(..., min_length=1, description="Specific, actionable coordination items")
    rationale: str = Field(..., description="Justification explaining why this balances national interests")
    predicted_votes: PredictedVotes = Field(default_factory=PredictedVotes, description="Predicted voting alignment")
    unresolved_issues: List[str] = Field(default_factory=list, description="Contested points requiring negotiation")
    supporting_countries: List[str] = Field(default_factory=list, description="Countries aligned with proposal")
    opposing_countries: List[str] = Field(default_factory=list, description="Countries with reservations or opposing")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Coordinator confidence score (0.0 to 1.0)")
    source: str = Field("llm_coordinator", description="'llm_coordinator' or 'deterministic_fallback'")
    status: str = Field("PROPOSED", description="Always PROPOSED; Coordinator cannot self-approve")

    # Traceability & Provenance
    model: Optional[str] = Field(None, description="Model identifier used")
    provider: Optional[str] = Field(None, description="LLM provider name")
    latency_ms: Optional[float] = Field(None, description="Inference latency in milliseconds")
    prompt_version: Optional[str] = Field(None, description="Prompt version tag")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return round(v, 4)

    @field_validator("status")
    @classmethod
    def validate_status_not_approved(cls, v: str) -> str:
        # Strict rule: Coordinator cannot self-approve
        if v.upper() in ["APPROVED", "PASSED", "ACCEPTED", "RESOLVED"]:
            raise ValueError("Coordinator cannot self-approve or mark proposals as APPROVED")
        return v


class CoordinatorContext(BaseModel):
    """
    Context provided to the Coordinator Agent.
    Strictly adheres to information containment: no hidden future events,
    no private country reasoning, no internal scratchpads.
    """
    simulation_id: str
    current_tick: int
    current_time: str
    crisis_id: str
    crisis_title: str
    crisis_summary: str
    current_event: Optional[Dict[str, Any]] = None
    public_event_history: List[str] = Field(default_factory=list)
    participating_countries: List[CountryPositionSummary] = Field(default_factory=list)
    aggregation: DeterministicAggregation
    past_proposals: List[Dict[str, Any]] = Field(default_factory=list)
    governance_frameworks: List[str] = Field(default_factory=list)

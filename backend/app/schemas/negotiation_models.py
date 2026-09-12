"""
Pydantic schemas and domain models for Negotiation & Voting Logic (Phase 6).
Includes Vote, ProposalVersion, VotingResult, NegotiationRound,
NegotiationOutcome, and NegotiationSession.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# SimulationMode type definition
SimulationMode = Literal["no_coordination", "partial", "coordinated"]

# Vote choices per rules.md Section 4: "Approve / Reject / Undecided"
VoteType = Literal["Approve", "Reject", "Undecided"]

NegotiationStatus = Literal[
    "PROPOSED",
    "NEGOTIATION_OPEN",
    "ROUND_ACTIVE",
    "POSITIONS_COLLECTED",
    "VOTING",
    "VOTE_EVALUATED",
    "REVISION_REQUIRED",
    "ACCEPTED",
    "PARTIAL_AGREEMENT",
    "FAILED",
    "BREAKDOWN",
    "MAX_ROUNDS_REACHED",
    "NO_QUORUM",
]


class Vote(BaseModel):
    """
    Structured vote cast by a country on a specific proposal version.
    """
    vote_id: str = Field(..., description="Unique identifier for this vote")
    country_id: str = Field(..., description="Country casting the vote")
    round: int = Field(..., ge=1, description="Negotiation round number")
    proposal_id: str = Field(..., description="Base proposal ID")
    proposal_version: int = Field(..., ge=1, description="Proposal version voted on")
    vote: VoteType = Field(..., description="Approve, Reject, or Undecided")
    rationale: str = Field(..., description="National strategic justification")
    conditions_requested: List[str] = Field(default_factory=list, description="Stipulations or conditions demanded")
    objections_raised: List[str] = Field(default_factory=list, description="Specific contested points")
    created_at_tick: int = Field(0, ge=0, description="Tick at which vote was recorded")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp"
    )

    @field_validator("vote", mode="before")
    @classmethod
    def normalize_vote(cls, v: Any) -> str:
        if isinstance(v, str):
            v_clean = v.strip().capitalize()
            if v_clean in ("Approve", "Approval", "Yes", "Support"):
                return "Approve"
            if v_clean in ("Reject", "Rejection", "No", "Oppose"):
                return "Reject"
            if v_clean in ("Undecided", "Abstain", "Abstention", "Conditional"):
                return "Undecided"
        return v


class ProposalVersion(BaseModel):
    """
    Auditable snapshot of a specific iteration of an international proposal.
    """
    version: int = Field(..., ge=1, description="Sequential version index (1, 2, 3...)")
    proposal_id: str = Field(..., description="Root proposal identifier")
    title: str = Field(..., description="Title of proposal version")
    summary: str = Field(..., description="Summary of proposed terms")
    items: List[str] = Field(..., min_length=1, description="Actionable multilateral items")
    rationale: str = Field(..., description="Justification balancing sovereignty and collective risk")
    revision_reason: Optional[str] = Field(None, description="Why this revision was created")
    unresolved_issues: List[str] = Field(default_factory=list, description="Remaining contested points")
    created_at_tick: int = Field(0, ge=0, description="Tick when version was drafted")
    source: str = Field("llm_coordinator", description="'llm_coordinator' or 'deterministic_fallback'")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp"
    )


class VotingResult(BaseModel):
    """
    Deterministic result of a round of voting under a specific coordination mode.
    """
    round: int = Field(..., ge=1, description="Round number evaluated")
    proposal_version: int = Field(..., ge=1, description="Proposal version evaluated")
    coordination_mode: SimulationMode = Field(..., description="Governing coordination mode")
    eligible_voters: int = Field(..., ge=0, description="Total eligible participating nations")
    votes_cast: int = Field(..., ge=0, description="Total votes submitted")
    votes_for: int = Field(..., ge=0, description="Total 'Approve' votes")
    votes_against: int = Field(..., ge=0, description="Total 'Reject' votes")
    abstentions: int = Field(..., ge=0, description="Total 'Undecided' votes")
    invalid_votes: int = Field(0, ge=0, description="Rejected or malformed votes")
    participation_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of eligible voters casting votes")
    is_quorum_met: bool = Field(..., description="Whether required participation threshold was reached")
    required_threshold: float = Field(..., ge=0.0, le=1.0, description="Approval fraction required to pass")
    achieved_threshold: float = Field(..., ge=0.0, le=1.0, description="Actual approval fraction achieved")
    passed: bool = Field(..., description="Whether proposal passed according to deterministic mode rules")
    status: Literal["PASSED", "FAILED", "NO_QUORUM", "TIE", "INSUFFICIENT_SUPPORT"] = Field(
        ..., description="Categorical evaluation status"
    )
    failure_reason: Optional[str] = Field(None, description="Explanation if proposal did not pass")
    approving_countries: List[str] = Field(default_factory=list, description="Country IDs voting Approve")
    opposing_countries: List[str] = Field(default_factory=list, description="Country IDs voting Reject")
    abstaining_countries: List[str] = Field(default_factory=list, description="Country IDs voting Undecided")


class NegotiationRound(BaseModel):
    """
    A discrete round in the negotiation process containing proposals, votes, and results.
    """
    round_number: int = Field(..., ge=1, description="Round index")
    proposal_version: ProposalVersion = Field(..., description="Proposal version voted upon")
    votes: Dict[str, Vote] = Field(default_factory=dict, description="Map of country_id to Vote")
    voting_result: Optional[VotingResult] = Field(None, description="Evaluated result of this round")
    unresolved_issues: List[str] = Field(default_factory=list, description="Objections carried forward")
    status: Literal["PENDING", "VOTING", "COMPLETED", "REVISION_REQUESTED"] = Field(
        "PENDING", description="Status of this specific round"
    )
    started_at_tick: int = Field(..., ge=0)
    completed_at_tick: Optional[int] = Field(None)


class NegotiationOutcome(BaseModel):
    """
    Final immutable outcome of the negotiation session delivered to the Simulation Engine.
    """
    negotiation_id: str = Field(..., description="Unique negotiation session ID")
    simulation_id: str = Field(..., description="Target simulation ID")
    coordination_mode: SimulationMode = Field(..., description="Governing coordination mode")
    final_status: Literal[
        "ACCEPTED",
        "PARTIAL_AGREEMENT",
        "FAILED",
        "BREAKDOWN",
        "MAX_ROUNDS_REACHED",
        "NO_QUORUM",
    ] = Field(..., description="Final outcome classification")
    agreement_reached: bool = Field(..., description="True if proposal passed (ACCEPTED or PARTIAL_AGREEMENT)")
    rounds_completed: int = Field(..., ge=1, description="Total rounds executed")
    final_proposal_version: int = Field(..., ge=1, description="Version of the final proposal")
    final_proposal: Optional[ProposalVersion] = Field(None, description="Final proposal terms")
    final_vote_result: Optional[VotingResult] = Field(None, description="Final vote tally")
    supporting_countries: List[str] = Field(default_factory=list, description="Nations endorsing final agreement")
    opposing_countries: List[str] = Field(default_factory=list, description="Nations dissenting")
    abstaining_countries: List[str] = Field(default_factory=list, description="Nations abstaining")
    unresolved_issues: List[str] = Field(default_factory=list, description="Issues remaining unresolved")
    failure_reason: Optional[str] = Field(None, description="Failure justification if not approved")
    completed_at_tick: int = Field(..., ge=0, description="Simulation tick when negotiation concluded")


class NegotiationSession(BaseModel):
    """
    Complete, auditable domain model representing an entire negotiation session.
    """
    negotiation_id: str = Field(..., description="Unique negotiation identifier")
    simulation_id: str = Field(..., description="Target simulation ID")
    scenario_id: str = Field(..., description="Scenario identifier")
    coordination_mode: SimulationMode = Field(..., description="Governing coordination mode")
    status: NegotiationStatus = Field("PROPOSED", description="Current lifecycle state")
    current_round: int = Field(1, ge=1, description="Current active round index")
    max_rounds: int = Field(3, ge=1, le=5, description="Maximum allowable rounds (default 3 per rules.md)")
    participating_countries: List[str] = Field(default_factory=list, description="Eligible country IDs")
    proposal_versions: List[ProposalVersion] = Field(default_factory=list, description="Complete version history")
    rounds: List[NegotiationRound] = Field(default_factory=list, description="Sequential round logs")
    outcome: Optional[NegotiationOutcome] = Field(None, description="Final outcome if completed")
    created_at_tick: int = Field(0, ge=0, description="Tick created")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO creation timestamp"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")

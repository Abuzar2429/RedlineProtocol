"""
Pydantic schemas for the Phase 2 Data Layer:
- Country data
- Crisis scenario data
- Governance document metadata and content
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Country Models ────────────────────────────────────────────────────────────

class CountryData(BaseModel):
    id: str = Field(..., description="Unique country identifier (e.g. country_01)")
    country_id: Optional[str] = Field(None, description="ISO-style or canonical identifier (mirrors id)")
    name: str = Field(..., description="Full country name (e.g. Federal Republic of Alerion)")
    flag_emoji: str = Field("🌐", description="Flag emoji representation")
    region: str = Field(..., description="Geographical or geopolitical region")
    government_type: str = Field(..., description="Form of government")
    population: int = Field(..., ge=0, description="Total population")

    # Quantified state capacities (0-100)
    economic_strength: int = Field(..., ge=0, le=100, description="Economic capacity index (0-100)")
    technology_capacity: int = Field(..., ge=0, le=100, description="General technological capacity (0-100)")
    ai_capability: int = Field(..., ge=0, le=100, description="Frontier AI capability index (0-100)")
    military_capacity: int = Field(..., ge=0, le=100, description="Defense and military capacity (0-100)")
    political_stability: int = Field(..., ge=0, le=100, description="Political stability index (0-100)")
    governance_capacity: int = Field(..., ge=0, le=100, description="Institutional governance capacity (0-100)")

    # Behavioral and diplomatic attributes
    risk_tolerance: Literal["low", "medium", "high"] = Field(..., description="Risk tolerance tier")
    transparency: Literal["low", "medium", "high"] = Field("medium", description="Transparency orientation")
    coordination_willingness: Literal["low", "medium", "high"] = Field("medium", description="Willingness to coordinate internationally")
    decision_speed: Literal["slow", "medium", "fast"] = Field("medium", description="Speed of institutional decision making")
    ai_capability_level: Literal["low", "medium", "high"] = Field("medium", description="AI tier level")
    diplomatic_influence: float = Field(..., ge=0.0, le=1.0, description="Normalized diplomatic influence (0.0 to 1.0)")
    international_influence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Mirrors diplomatic_influence")
    geopolitical_bloc: Optional[str] = Field(None, description="Geopolitical bloc alliance")

    # Policy and priorities
    strategic_priorities: List[str] = Field(default_factory=list, description="List of strategic priorities")
    priorities: Optional[List[str]] = Field(None, description="Mirrors strategic_priorities")
    allies: List[str] = Field(default_factory=list, description="List of allied country IDs")
    rivals: List[str] = Field(default_factory=list, description="List of rival country IDs")
    ai_policy_position: str = Field(..., description="Narrative describing state's AI doctrine")
    initial_relationships: Dict[str, int] = Field(default_factory=dict, description="Initial bilateral scores (-100 to 100)")

    @model_validator(mode="after")
    def populate_aliases_and_defaults(self) -> "CountryData":
        if not self.country_id:
            self.country_id = self.id
        if self.priorities is None:
            self.priorities = list(self.strategic_priorities)
        if self.international_influence is None:
            self.international_influence = self.diplomatic_influence
        return self

    @field_validator("initial_relationships")
    @classmethod
    def validate_relationship_scores(cls, v: Dict[str, int]) -> Dict[str, int]:
        for cid, score in v.items():
            if not (-100 <= score <= 100):
                raise ValueError(f"Relationship score for {cid} must be between -100 and 100, got {score}")
        return v


# ── Scenario Models ───────────────────────────────────────────────────────────

class TimelineEvent(BaseModel):
    time_offset: int = Field(..., ge=0, description="Time offset in minutes from scenario start")
    event: str = Field(..., description="Event description")
    type: Literal["detection", "spread", "escalation", "media", "diplomatic", "resolution"] = Field(
        ..., description="Event category"
    )


class ScenarioAction(BaseModel):
    id: str = Field(..., description="Action identifier")
    label: str = Field(..., description="Human-readable label")
    risk_reduction_value: float = Field(..., description="Impact on baseline risk")
    coordination_effect: float = Field(..., description="Impact on multilateral coordination")
    requires_agreement: bool = Field(False, description="Whether multilateral consensus is required")
    visibility: Literal["public", "private", "bilateral"] = Field("public", description="Action visibility")


class ScenarioData(BaseModel):
    id: str = Field(..., description="Unique scenario identifier (e.g. scenario_01)")
    scenario_id: Optional[str] = Field(None, description="Mirrors id or canonical crisis code")
    title: str = Field(..., description="Scenario title")
    description: str = Field(..., description="Detailed description of the crisis")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity category")
    severity_score: float = Field(..., ge=0.0, le=1.0, description="Quantified severity score (0.0 to 1.0)")

    affected_countries: List[str] = Field(..., min_length=1, description="List of affected country IDs")
    origin_country: str = Field(..., description="Country ID where the crisis originated")

    information_delay: Dict[str, int] = Field(
        default_factory=dict, description="Delay in minutes per country before receiving initial information"
    )

    timeline: List[TimelineEvent] = Field(..., min_length=1, description="Sequence of scenario timeline events")

    initial_evidence_completeness: float = Field(
        ..., ge=0.0, le=1.0, description="Starting evidence completeness fraction (0.0 to 1.0)"
    )
    evidence_grows_at: float = Field(
        ..., ge=0.0, le=1.0, description="Rate of evidence growth per minute/tick"
    )

    potential_impacts: List[str] = Field(default_factory=list, description="Impact domains")
    available_actions: List[ScenarioAction] = Field(..., min_length=1, description="Available policy/crisis actions")
    governance_docs_relevant: List[str] = Field(
        default_factory=list, description="IDs of relevant governance knowledge documents"
    )

    @model_validator(mode="after")
    def populate_scenario_aliases(self) -> "ScenarioData":
        if not self.scenario_id:
            self.scenario_id = self.id
        return self


# ── Governance Document Models ────────────────────────────────────────────────

class GovernanceDocumentMetadata(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    category: Literal["principles", "response", "cooperation", "data_sharing", "emergency", "liability", "strategy"] = Field(
        ..., description="Document category"
    )
    relevance_tags: List[str] = Field(default_factory=list, description="Domain topic tags")
    version: str = Field("1.0", description="Document version")
    effective_date: Optional[str] = Field(None, description="Fictional ratification/effective date")


class GovernanceDocument(BaseModel):
    metadata: GovernanceDocumentMetadata
    content: str = Field(..., description="Full markdown text of the governance document")
    sections: Dict[str, str] = Field(default_factory=dict, description="Parsed heading sections")

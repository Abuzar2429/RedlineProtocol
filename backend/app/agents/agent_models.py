"""
Pydantic schemas for Country Agent decision input/output.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CountryDecisionResponse(BaseModel):
    """
    Structured response model returned by the LLM Country Agent.
    """
    action_id: str = Field(..., description="Action ID chosen from the scenario's available actions")
    reasoning: str = Field(..., description="Detailed rationale explaining the decision based on national priorities")
    risks: List[str] = Field(default_factory=list, description="Key operational or diplomatic risks noted")
    expected_reactions: str = Field("", description="Anticipated reactions from allies and rivals")
    willingness_to_coordinate: float = Field(0.5, ge=0.0, le=1.0, description="Willingness to coordinate (0.0 to 1.0)")

    # Backwards compatibility / alias support for LLM variations
    decision: Optional[str] = Field(None, description="Optional alias for action_id")
    justification: Optional[str] = Field(None, description="Optional alias for reasoning")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "action_id" not in data and "decision" in data:
                data["action_id"] = data["decision"]
            if "reasoning" not in data and "justification" in data:
                data["reasoning"] = data["justification"]
            if "willingness_to_coordinate" not in data and "confidence" in data:
                data["willingness_to_coordinate"] = data["confidence"]
        return data

    @field_validator("action_id")
    @classmethod
    def validate_action_id_not_empty(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("action_id cannot be empty")
        return v_clean


class DecisionContext(BaseModel):
    """
    Information boundary object: contains ONLY the data that the specific
    country is authorized to know at the current simulation tick.
    """
    country_id: str
    country_name: str
    current_tick: int
    current_time: str
    crisis_title: str
    crisis_description: str
    awareness_status: str
    evidence_completeness_pct: float
    national_priorities: List[str]
    risk_tolerance: str
    coordination_willingness: str
    ai_policy_position: str
    known_public_events: List[str]
    available_actions: List[Dict[str, Any]]
    allies: List[str]
    rivals: List[str]
    rag_context: str = Field("", description="Retrieved governance framework excerpts (Phase 9)")
    rag_sources: List[str] = Field(default_factory=list, description="Citations of retrieved governance documents (Phase 9)")

"""
Crisis scenario data endpoints (Phase 2 & Dynamic Custom Scenarios).
"""
import re
import uuid
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import yaml

from app.schemas.data_models import ScenarioAction, ScenarioData, TimelineEvent
from app.services.data_loader import default_data_loader

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


class CreateCustomScenarioRequest(BaseModel):
    """
    Request model for user-defined custom crisis scenarios.
    Allows users to input any crisis problem prompt, and have the system
    generate a fully functional simulation scenario.
    """
    title: str = Field(..., min_length=3, description="Headline or crisis title")
    description: str = Field(..., min_length=10, description="Full description of the crisis or problem")
    severity: Literal["low", "medium", "high", "critical"] = Field("high", description="Severity level")
    severity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Numerical severity (0.0 to 1.0)")
    origin_country: Optional[str] = Field("country_01", description="Originating nation ID")
    affected_countries: Optional[List[str]] = Field(None, description="List of affected country IDs")
    timeline: Optional[List[Dict[str, Any]]] = Field(None, description="Custom sequence of timeline events")
    available_actions: Optional[List[Dict[str, Any]]] = Field(None, description="Custom policy actions")


@router.get("", response_model=List[ScenarioData])
async def list_scenarios() -> List[ScenarioData]:
    """
    Returns the list of all available crisis scenarios for the simulator.
    """
    try:
        return default_data_loader.load_all_scenarios()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load crisis scenarios: {str(exc)}",
        )


@router.post("", response_model=ScenarioData, status_code=status.HTTP_201_CREATED)
async def create_custom_scenario(req: CreateCustomScenarioRequest) -> ScenarioData:
    """
    Creates a new custom crisis scenario dynamically from user-provided text.
    The AIs will evaluate and make decisions based on this custom scenario.
    """
    try:
        # Generate safe slug and unique ID
        clean_title = re.sub(r"[^a-zA-Z0-9]+", "_", req.title.lower()).strip("_")[:24]
        if not clean_title:
            clean_title = "custom_crisis"
        unique_suffix = uuid.uuid4().hex[:6]
        scenario_id = f"custom_{clean_title}_{unique_suffix}"

        # Severity score mapping if omitted
        score_map = {"low": 0.35, "medium": 0.60, "high": 0.82, "critical": 0.94}
        sev_score = req.severity_score if req.severity_score is not None else score_map.get(req.severity, 0.80)

        # Affected countries
        all_countries = default_data_loader.load_all_countries()
        all_country_ids = [c.id for c in all_countries]

        origin = req.origin_country if req.origin_country in all_country_ids else (all_country_ids[0] if all_country_ids else "country_01")
        affected = req.affected_countries if req.affected_countries else all_country_ids

        # Information delays
        delays = {origin: 0}
        for i, cid in enumerate(all_country_ids):
            if cid != origin:
                delays[cid] = min(20, (i + 1) * 2)

        # Timeline
        if req.timeline:
            timeline_events = [TimelineEvent.model_validate(e) for e in req.timeline]
        else:
            timeline_events = [
                TimelineEvent(
                    time_offset=0,
                    event=f"Initial anomaly detected: {req.title}. Local sensors record erratic autonomous model telemetry.",
                    type="detection",
                ),
                TimelineEvent(
                    time_offset=3,
                    event="Autonomous contagion spreads across digital routing gateways into regional sovereign infrastructure.",
                    type="spread",
                ),
                TimelineEvent(
                    time_offset=6,
                    event="Neighboring national cyber command centers log anomalous payloads and request official clarification.",
                    type="escalation",
                ),
                TimelineEvent(
                    time_offset=10,
                    event="Global international press breaks verified reports of systemic algorithmic instability.",
                    type="media",
                ),
                TimelineEvent(
                    time_offset=15,
                    event="Multilateral crisis clearinghouse convenes emergency diplomatic session to establish joint containment.",
                    type="diplomatic",
                ),
                TimelineEvent(
                    time_offset=25,
                    event="Session reaches critical inflection point: states must vote on binding collective containment accords.",
                    type="resolution",
                ),
            ]

        # Available actions
        if req.available_actions:
            actions = [ScenarioAction.model_validate(a) for a in req.available_actions]
        else:
            actions = [
                ScenarioAction(
                    id="do_nothing",
                    label="Do Nothing / Await Further Evidence",
                    risk_reduction_value=0.0,
                    coordination_effect=-0.1,
                    requires_agreement=False,
                    visibility="private",
                ),
                ScenarioAction(
                    id="investigate_internally",
                    label="Conduct Internal Sovereign Forensic Investigation",
                    risk_reduction_value=-5.0,
                    coordination_effect=0.0,
                    requires_agreement=False,
                    visibility="private",
                ),
                ScenarioAction(
                    id="notify_affected",
                    label="Issue Official Early Warning to Affected Neighboring States",
                    risk_reduction_value=-15.0,
                    coordination_effect=0.25,
                    requires_agreement=False,
                    visibility="public",
                ),
                ScenarioAction(
                    id="suspend_ai_system",
                    label="Execute Sovereign Emergency Circuit-Breaker / Suspend System",
                    risk_reduction_value=-25.0,
                    coordination_effect=0.15,
                    requires_agreement=False,
                    visibility="public",
                ),
                ScenarioAction(
                    id="request_multilateral_audit",
                    label="Request Joint Multilateral Technical Audit Team",
                    risk_reduction_value=-20.0,
                    coordination_effect=0.35,
                    requires_agreement=True,
                    visibility="public",
                ),
                ScenarioAction(
                    id="share_technical_evidence",
                    label="Share Unredacted System Telemetry and Model Execution Logs",
                    risk_reduction_value=-15.0,
                    coordination_effect=0.30,
                    requires_agreement=False,
                    visibility="bilateral",
                ),
                ScenarioAction(
                    id="impose_temporary_restrictions",
                    label="Impose Temporary Border Gateway Interruption and Firewall Isolation",
                    risk_reduction_value=-10.0,
                    coordination_effect=-0.15,
                    requires_agreement=False,
                    visibility="public",
                ),
                ScenarioAction(
                    id="ratify_joint_containment",
                    label="Ratify Multilateral Joint Containment and Recovery Accord",
                    risk_reduction_value=-35.0,
                    coordination_effect=0.50,
                    requires_agreement=True,
                    visibility="public",
                ),
            ]

        scenario = ScenarioData(
            id=scenario_id,
            scenario_id=scenario_id,
            title=req.title,
            description=req.description,
            severity=req.severity,
            severity_score=sev_score,
            affected_countries=affected,
            origin_country=origin,
            information_delay=delays,
            timeline=timeline_events,
            initial_evidence_completeness=0.35,
            evidence_grows_at=0.04,
            potential_impacts=["infrastructure", "national_security", "public_trust", "sovereignty"],
            available_actions=actions,
            governance_docs_relevant=[
                "emergency_procedures",
                "incident_response",
                "data_sharing_protocols",
                "international_cooperation",
            ],
        )

        # Save to YAML
        target_path = default_data_loader.scenarios_dir / f"{scenario_id}.yaml"
        scenario_dict = scenario.model_dump()
        with open(target_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(scenario_dict, f, sort_keys=False, allow_unicode=True)

        return scenario

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom scenario: {str(exc)}",
        )


@router.get("/{scenario_id}", response_model=ScenarioData)
async def get_scenario(scenario_id: str) -> ScenarioData:
    """
    Retrieves the structured specification for a specific crisis scenario by ID (e.g. 'scenario_01' or 'crisis_001').
    """
    try:
        return default_data_loader.load_scenario(scenario_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving scenario '{scenario_id}': {str(exc)}",
        )

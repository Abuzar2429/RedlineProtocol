"""
Decision Context Builder enforcing strict information boundaries for Country Agents.
"""
from typing import Any, Dict, List, Optional

from app.agents.agent_models import DecisionContext
from app.schemas.data_models import CountryData, ScenarioData
from app.schemas.simulation_models import SimulationState


class DecisionContextBuilder:
    """
    Constructs an isolated decision context for a country agent,
    strictly omitting unauthorized or future simulation state.
    """

    @classmethod
    def build_context(
        cls,
        country: CountryData,
        state: SimulationState,
        scenario: ScenarioData,
        rag_context: str = "",
        rag_sources: Optional[List[str]] = None,
    ) -> DecisionContext:
        country_state = state.countries.get(country.id)
        awareness_status = country_state.status if country_state else "Unaware"
        evidence_pct = (country_state.information_completeness * 100.0) if country_state else 0.0

        # Filter event history: ONLY events that occurred at or before current_tick,
        # and are either public OR explicitly involve this country.
        # Future events and other countries' private internal events are strictly excluded.
        known_events: List[str] = []
        for ev in state.event_history:
            if ev.tick > state.current_tick:
                continue  # Reject future events

            is_targeted = country.id in ev.affected_countries or ev.source == country.id
            is_public_timeline = ev.event_type in ("TIMELINE_EVENT", "CRISIS_TRIGGERED", "CRISIS_ESCALATION", "CRISIS_RESOLVED")
            is_public_policy = ev.event_type == "POLICY_ACTION" and ev.payload.get("visibility", "public") == "public"

            if is_targeted or is_public_timeline or is_public_policy:
                known_events.append(f"[{state.current_time}] {ev.description}")

        # Keep last 6 relevant public events to prevent prompt bloat
        recent_events = known_events[-6:]

        available_actions: List[Dict[str, Any]] = [
            action.model_dump() for action in scenario.available_actions
        ]

        return DecisionContext(
            country_id=country.id,
            country_name=country.name,
            current_tick=state.current_tick,
            current_time=state.current_time,
            crisis_title=state.crisis_state.title,
            crisis_description=scenario.description,
            awareness_status=awareness_status,
            evidence_completeness_pct=evidence_pct,
            national_priorities=list(country.strategic_priorities),
            risk_tolerance=country.risk_tolerance,
            coordination_willingness=country.coordination_willingness,
            ai_policy_position=country.ai_policy_position,
            known_public_events=recent_events,
            available_actions=available_actions,
            allies=list(country.allies),
            rivals=list(country.rivals),
            rag_context=rag_context,
            rag_sources=rag_sources or [],
        )

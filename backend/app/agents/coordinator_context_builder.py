"""
Coordinator Context Builder enforcing strict information boundaries for Phase 5.
Extracts only validated, shareable country positions and public crisis data.
"""
from typing import Any, Dict, List, Optional
from collections import Counter

from app.agents.coordinator_models import (
    CoordinatorContext,
    CountryPositionSummary,
    DeterministicAggregation,
)
from app.schemas.simulation_models import DecisionRecord, SimulationEvent, SimulationState


class CoordinatorContextBuilder:
    """
    Constructs the isolated context for the International Coordinator Agent.
    Strictly omits:
      - Hidden future events (ev.tick > current_tick)
      - Country internal chain-of-thought and private justifications
      - Secret/unrevealed scenario facts
      - Uncalculated final scoring metrics
    """

    @classmethod
    def build_context(
        cls,
        state: SimulationState,
        current_event: Optional[SimulationEvent] = None,
        country_catalog: Optional[Dict[str, Any]] = None,
    ) -> CoordinatorContext:
        current_tick = state.current_tick

        # 1. Filter public events (Strictly tick <= current_tick)
        public_events: List[str] = []
        for ev in state.event_history:
            if ev.tick > current_tick:
                continue  # Never leak future events
            if ev.event_type in (
                "TIMELINE_EVENT",
                "CRISIS_TRIGGERED",
                "COORDINATION_REQUEST",
                "CRISIS_ESCALATION",
                "CRISIS_DE_ESCALATION",
                "CRISIS_RESOLVED",
            ) or (ev.event_type == "POLICY_ACTION" and ev.payload.get("visibility") == "public"):
                public_events.append(f"[T+{ev.tick:02d}] {ev.description}")

        recent_public_events = public_events[-8:]

        # 2. Extract latest validated decision per country
        latest_decisions: Dict[str, DecisionRecord] = {}
        for d in state.decisions:
            if d.tick <= current_tick:
                # Keep latest decision
                latest_decisions[d.country_id] = d

        # 3. Build shareable country position summaries
        participating_countries: List[CountryPositionSummary] = []
        action_counter: Counter = Counter()
        high_coord = 0
        mod_coord = 0
        low_coord = 0
        aware_count = 0

        for country_id, c_state in sorted(state.countries.items()):
            is_aware = c_state.status != "Unaware"
            if is_aware:
                aware_count += 1

            country_name = country_id.replace("_", " ").title()
            if country_catalog and country_id in country_catalog:
                country_name = getattr(country_catalog[country_id], "name", country_name)

            decision = latest_decisions.get(country_id)
            if decision:
                action_id = decision.action_id
                action_name = decision.action_id.replace("_", " ").title()
                willingness = decision.willingness_to_coordinate if decision.willingness_to_coordinate is not None else 0.50
                # Split comma/semicolon separated risk notes if string
                risks: List[str] = []
                if decision.risks_noted:
                    risks = [r.strip() for r in decision.risks_noted.split(";") if r.strip()]
                    if not risks:
                        risks = [decision.risks_noted.strip()]
                action_counter[action_id] += 1
            else:
                action_id = "awaiting_position" if is_aware else "unaware"
                action_name = "Awaiting Position" if is_aware else "Unaware"
                willingness = 0.50 if is_aware else 0.0
                risks = []
                if is_aware:
                    action_counter["awaiting_position"] += 1

            if willingness >= 0.70:
                high_coord += 1
            elif willingness >= 0.40:
                mod_coord += 1
            else:
                low_coord += 1

            participating_countries.append(
                CountryPositionSummary(
                    country_id=country_id,
                    country_name=country_name,
                    status=c_state.status,
                    action_id=action_id,
                    action_name=action_name,
                    willingness_to_coordinate=willingness,
                    risks_noted=risks,
                    conditions=[],
                )
            )

        # 4. Code-owned deterministic aggregation
        majority_act = action_counter.most_common(1)[0][0] if action_counter else None
        aggregation = DeterministicAggregation(
            total_countries=len(state.countries),
            aware_countries=aware_count,
            action_counts=dict(action_counter),
            high_coordination_count=high_coord,
            moderate_coordination_count=mod_coord,
            low_coordination_count=low_coord,
            majority_action=majority_act,
        )

        # 5. Extract past proposals
        past_proposals_list: List[Dict[str, Any]] = []
        if hasattr(state, "proposals") and state.proposals:
            for p in state.proposals:
                past_proposals_list.append({
                    "proposal_id": p.proposal_id,
                    "round": p.round,
                    "title": p.title,
                    "status": p.status,
                    "tick": p.tick,
                })

        # 6. Current event payload
        current_event_dict = None
        if current_event:
            ev_title = getattr(current_event, "title", None) or current_event.payload.get("title", current_event.description[:40])
            current_event_dict = {
                "event_id": current_event.event_id,
                "event_type": current_event.event_type,
                "title": ev_title,
                "description": current_event.description,
            }

        crisis_summary = getattr(state.crisis_state, "summary", None) or state.crisis_state.title

        return CoordinatorContext(
            simulation_id=state.simulation_id,
            current_tick=current_tick,
            current_time=state.current_time,
            crisis_id=state.scenario_id,
            crisis_title=state.crisis_state.title,
            crisis_summary=crisis_summary,
            current_event=current_event_dict,
            public_event_history=recent_public_events,
            participating_countries=participating_countries,
            aggregation=aggregation,
            past_proposals=past_proposals_list,
            governance_frameworks=[
                "Multilateral AI Incident Response Framework (MAIRF)",
                "Charter for International Algorithmic Safety (CIAS)",
            ],
        )

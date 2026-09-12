"""
Event Processor and State Machine for AI Governance Crisis Simulator.

Dispatches simulation events to dedicated typed handlers:
- Enforces strictly sequential country status: Unaware -> Investigating -> Notified -> Coordinating
- Applies information delay gating
- Evaluates deterministic decisions
- Records state mutations and schedules descendant events
"""
import logging
import uuid
from typing import Dict, List, Optional

from app.schemas.data_models import CountryData, ScenarioAction, ScenarioData
from app.schemas.simulation_models import (
    CountrySimulationState,
    CrisisOperationalState,
    DecisionRecord,
    SimulationEvent,
    SimulationEventType,
    SimulationState,
)
from app.services.simulation.decision_maker import DeterministicDecisionMaker
from app.services.simulation.event_queue import EventQueue

logger = logging.getLogger(__name__)


class EventProcessor:
    """
    Handles event execution and state mutation in a strictly deterministic manner.
    """

    def __init__(
        self,
        scenario: ScenarioData,
        countries_map: Dict[str, CountryData],
        event_queue: EventQueue,
    ):
        self.scenario = scenario
        self.countries_map = countries_map
        self.event_queue = event_queue

    def process_event(
        self,
        event: SimulationEvent,
        state: SimulationState,
    ) -> List[SimulationEvent]:
        """
        Dispatches a single event, mutates simulation state,
        and schedules any new descendant events. Returns newly scheduled events.
        """
        handler_map = {
            "CRISIS_TRIGGERED": self._handle_crisis_triggered,
            "TIMELINE_EVENT": self._handle_timeline_event,
            "INFORMATION_RECEIVED": self._handle_information_received,
            "COUNTRY_NOTIFICATION": self._handle_country_notification,
            "DECISION_REQUIRED": self._handle_decision_required,
            "POLICY_ACTION": self._handle_policy_action,
            "COORDINATION_REQUEST": self._handle_coordination_request,
            "CRISIS_ESCALATION": self._handle_crisis_escalation,
            "CRISIS_DE_ESCALATION": self._handle_crisis_de_escalation,
            "CRISIS_RESOLVED": self._handle_crisis_resolved,
        }

        handler = handler_map.get(event.event_type)
        if not handler:
            logger.warning("No handler for event type %s; skipping", event.event_type)
            return []

        new_events = handler(event, state)
        for ne in new_events:
            self.event_queue.schedule(ne)

        return new_events

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _handle_crisis_triggered(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        """
        Initializes scenario activation at tick 0.
        """
        new_events: List[SimulationEvent] = []
        origin_id = self.scenario.origin_country

        state.crisis_state.phase = "DETECTION"

        # Origin country immediately transitions Unaware -> Investigating
        if origin_id in state.countries:
            c_state = state.countries[origin_id]
            c_state.status = "Investigating"
            c_state.aware = True
            c_state.information_completeness = max(0.5, self.scenario.initial_evidence_completeness)
            c_state.last_updated_tick = event.tick

            # Schedule origin country notification and decision
            new_events.append(
                SimulationEvent(
                    event_id=f"notif_{origin_id}_{event.tick + 1}",
                    tick=event.tick + 1,
                    priority=2,
                    event_type="COUNTRY_NOTIFICATION",
                    source="engine",
                    affected_countries=[origin_id],
                    description=f"{c_state.name} internal monitoring team confirms active anomaly.",
                    payload={"country_id": origin_id},
                )
            )

        # Schedule information arrival for all other affected countries based on delay
        for cid, delay in self.scenario.information_delay.items():
            if cid == origin_id:
                continue
            if cid in state.countries:
                new_events.append(
                    SimulationEvent(
                        event_id=f"info_{cid}_{delay}",
                        tick=delay,
                        priority=5,
                        event_type="INFORMATION_RECEIVED",
                        source="scenario_delay",
                        affected_countries=[cid],
                        description=f"{state.countries[cid].name} receives preliminary telemetry data (T+{delay:02d}).",
                        payload={"country_id": cid, "delay": delay},
                    )
                )

        # Schedule author-defined timeline events
        for te in self.scenario.timeline:
            if te.time_offset > 0:
                new_events.append(
                    SimulationEvent(
                        event_id=f"timeline_{te.time_offset}_{te.type}",
                        tick=te.time_offset,
                        priority=3,
                        event_type="TIMELINE_EVENT",
                        source="scenario_timeline",
                        affected_countries=self.scenario.affected_countries,
                        description=te.event,
                        payload={"timeline_type": te.type, "event": te.event},
                    )
                )

        return new_events

    def _handle_information_received(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        """
        Unlocks country awareness when information arrives after information_delay.
        Enforces sequential transition: Unaware -> Investigating
        """
        new_events: List[SimulationEvent] = []
        cid = event.payload.get("country_id")
        if not cid or cid not in state.countries:
            return new_events

        c_state = state.countries[cid]

        # Sequential status progression: Unaware -> Investigating
        if c_state.status == "Unaware":
            c_state.status = "Investigating"
            c_state.aware = True
            c_state.information_completeness = self.scenario.initial_evidence_completeness
            c_state.last_updated_tick = event.tick

            # Next step in sequence: Investigating -> Notified at tick + 1
            new_events.append(
                SimulationEvent(
                    event_id=f"notif_{cid}_{event.tick + 1}",
                    tick=event.tick + 1,
                    priority=4,
                    event_type="COUNTRY_NOTIFICATION",
                    source="engine",
                    affected_countries=[cid],
                    description=f"{c_state.name} emergency crisis panel receives verified notification.",
                    payload={"country_id": cid},
                )
            )

        return new_events

    def _handle_country_notification(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        """
        Enforces sequential transition: Investigating -> Notified
        Schedules decision event.
        """
        new_events: List[SimulationEvent] = []
        cid = event.payload.get("country_id")
        if not cid or cid not in state.countries:
            return new_events

        c_state = state.countries[cid]
        if c_state.status == "Investigating":
            c_state.status = "Notified"
            c_state.last_updated_tick = event.tick

            # Schedule decision point
            new_events.append(
                SimulationEvent(
                    event_id=f"dec_req_{cid}_{event.tick + 1}",
                    tick=event.tick + 1,
                    priority=3,
                    event_type="DECISION_REQUIRED",
                    source="engine",
                    affected_countries=[cid],
                    description=f"Action decision point reached for {c_state.name}.",
                    payload={"country_id": cid},
                )
            )

        return new_events

    def _handle_decision_required(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        """
        Evaluates deterministic decision for notified country and records decision.
        """
        new_events: List[SimulationEvent] = []
        cid = event.payload.get("country_id")
        if not cid or cid not in state.countries:
            return new_events

        country_data = self.countries_map.get(cid)
        c_state = state.countries[cid]
        if not country_data:
            return new_events

        # Evaluate deterministic decision
        decision = DeterministicDecisionMaker.evaluate_decision(
            simulation_id=state.simulation_id,
            country=country_data,
            country_state=c_state,
            available_actions=self.scenario.available_actions,
            tick=event.tick,
        )

        state.decisions.append(decision)
        c_state.decision_count += 1
        c_state.last_updated_tick = event.tick

        # Schedule execution of policy action
        new_events.append(
            SimulationEvent(
                event_id=f"policy_{cid}_{event.tick}_{decision.action_id}",
                tick=event.tick,
                priority=2,
                event_type="POLICY_ACTION",
                source=cid,
                affected_countries=[cid],
                description=f"{c_state.name} orders policy response: {decision.label}.",
                payload={
                    "country_id": cid,
                    "action_id": decision.action_id,
                    "label": decision.label,
                    "decision_id": decision.decision_id,
                },
            )
        )

        return new_events

    def _handle_policy_action(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        """
        Applies action effect to state.
        Enforces sequential transition: Notified -> Coordinating (if cooperative)
        Updates operational crisis risk.
        """
        new_events: List[SimulationEvent] = []
        cid = event.payload.get("country_id")
        action_id = event.payload.get("action_id")

        if not cid or cid not in state.countries:
            return new_events

        c_state = state.countries[cid]
        c_state.current_action = event.payload.get("label", action_id)

        # Lookup action details
        action = next((a for a in self.scenario.available_actions if a.id == action_id), None)
        if action:
            # Sequential progression to Coordinating if action involves coordination
            if action.coordination_effect > 0 or action.requires_agreement:
                if c_state.status == "Notified":
                    c_state.status = "Coordinating"
                    c_state.coordination_status = "Aligned"
                    c_state.last_updated_tick = event.tick
            elif action.coordination_effect < 0:
                c_state.coordination_status = "Unilateral"

            # Apply risk reduction (prevent negative risk)
            # risk_reduction_value is typically negative (e.g. -25 means risk drops by 25)
            risk_change = action.risk_reduction_value
            state.crisis_state.current_risk = max(
                10.0, min(100.0, state.crisis_state.current_risk + risk_change)
            )

        return new_events

    def _handle_timeline_event(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        """
        Updates scenario phase from narrative timeline events.
        """
        new_events: List[SimulationEvent] = []
        t_type = event.payload.get("timeline_type", "")

        if t_type == "spread":
            state.crisis_state.phase = "SPREAD"
        elif t_type in ("escalation", "media"):
            state.crisis_state.phase = "ESCALATION"
        elif t_type == "diplomatic":
            state.crisis_state.phase = "NEGOTIATION"
            # Trigger coordination request
            new_events.append(
                SimulationEvent(
                    event_id=f"coord_req_{event.tick}",
                    tick=event.tick,
                    priority=3,
                    event_type="COORDINATION_REQUEST",
                    source="engine",
                    affected_countries=self.scenario.affected_countries,
                    description="Multilateral coordination summit opens for joint response negotiation.",
                    payload={"trigger_tick": event.tick},
                )
            )
        elif t_type == "resolution":
            state.crisis_state.phase = "RESOLUTION"
            # Schedule resolution if timeline reached end
            max_offset = max(te.time_offset for te in self.scenario.timeline)
            if event.tick >= max_offset:
                new_events.append(
                    SimulationEvent(
                        event_id=f"resolved_{event.tick + 2}",
                        tick=event.tick + 2,
                        priority=1,
                        event_type="CRISIS_RESOLVED",
                        source="engine",
                        affected_countries=self.scenario.affected_countries,
                        description="Crisis response phase concluded; resolution accord ratified.",
                        payload={"resolved_at_tick": event.tick + 2},
                    )
                )

        return new_events

    def _handle_coordination_request(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        state.crisis_state.phase = "NEGOTIATION"
        return []

    def _handle_crisis_escalation(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        state.crisis_state.phase = "ESCALATION"
        state.crisis_state.current_risk = min(100.0, state.crisis_state.current_risk + 10.0)
        return []

    def _handle_crisis_de_escalation(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        state.crisis_state.current_risk = max(10.0, state.crisis_state.current_risk - 15.0)
        return []

    def _handle_crisis_resolved(
        self, event: SimulationEvent, state: SimulationState
    ) -> List[SimulationEvent]:
        state.crisis_state.phase = "RESOLVED"
        state.status = "COMPLETED"
        return []

"""
Core Simulation Engine for AI Governance Crisis Simulator.

Orchestrates the deterministic simulation lifecycle:
- Initialization from Phase 2 scenario and country datasets
- Virtual clock advancement
- Event queue popping & EventProcessor dispatch
- State mutation and history logging
- Single-step and run-until-complete execution modes
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.schemas.data_models import CountryData, ScenarioData
from app.schemas.simulation_models import (
    CountrySimulationState,
    CrisisOperationalState,
    SimulationEvent,
    SimulationMode,
    SimulationState,
    SimulationStatus,
    SimulationStepResponse,
)
from app.services.data_loader import default_data_loader
from app.services.simulation.clock import SimulationClock
from app.services.simulation.event_processor import EventProcessor
from app.services.simulation.event_queue import EventQueue

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Stateful, deterministic execution engine for a single simulation run.
    """

    def __init__(
        self,
        scenario: ScenarioData,
        countries: List[CountryData],
        mode: SimulationMode = "coordinated",
        simulation_id: Optional[str] = None,
        max_ticks: int = 120,
        decision_service: Optional[Any] = None,
    ):
        self.scenario = scenario
        self.countries_map: Dict[str, CountryData] = {c.id: c for c in countries}
        self.mode = mode
        self.max_ticks = max_ticks
        self.simulation_id = simulation_id or f"sim_{uuid.uuid4().hex[:12]}"

        # Initialize Virtual Clock
        self.clock = SimulationClock(initial_tick=0)

        # Initialize Event Queue
        self.event_queue = EventQueue()

        # Initialize Event Processor
        self.event_processor = EventProcessor(
            scenario=self.scenario,
            countries_map=self.countries_map,
            event_queue=self.event_queue,
            decision_service=decision_service,
        )

        # Build initial simulation state
        self.state = self._build_initial_state()

        # Seed the initial trigger event at tick 0
        self._seed_initial_events()

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        scenario_id: str,
        mode: SimulationMode = "coordinated",
        simulation_id: Optional[str] = None,
        max_ticks: int = 120,
        decision_service: Optional[Any] = None,
    ) -> "SimulationEngine":
        """
        Factory method to initialize an engine using the Phase 2 DataLoader.
        """
        scenario = default_data_loader.load_scenario(scenario_id)
        countries = default_data_loader.load_all_countries()

        return cls(
            scenario=scenario,
            countries=countries,
            mode=mode,
            simulation_id=simulation_id,
            max_ticks=max_ticks,
            decision_service=decision_service,
        )

    # ── Initialization Helpers ────────────────────────────────────────────────

    def _build_initial_state(self) -> SimulationState:
        """
        Constructs the pristine starting state from scenario and country profiles.
        """
        country_states: Dict[str, CountrySimulationState] = {}
        relationships: Dict[str, Dict[str, int]] = {}

        for cid, c in self.countries_map.items():
            # Initial country status is Unaware
            country_states[cid] = CountrySimulationState(
                country_id=cid,
                name=c.name,
                status="Unaware",
                aware=False,
                information_completeness=0.0,
                current_action=None,
                coordination_status="Independent",
                decision_count=0,
                last_updated_tick=0,
            )
            relationships[cid] = dict(c.initial_relationships)

        crisis_state = CrisisOperationalState(
            scenario_id=self.scenario.id,
            title=self.scenario.title,
            severity=self.scenario.severity,
            severity_score=self.scenario.severity_score,
            current_risk=100.0,
            phase="DETECTION",
            origin_country=self.scenario.origin_country,
            affected_countries=list(self.scenario.affected_countries),
            impact_domains=list(self.scenario.potential_impacts),
        )

        return SimulationState(
            simulation_id=self.simulation_id,
            scenario_id=self.scenario.id,
            mode=self.mode,
            status="CREATED",
            current_tick=0,
            current_time="T+00",
            crisis_state=crisis_state,
            countries=country_states,
            relationships=relationships,
            active_events=[],
            pending_decisions=[],
            decisions=[],
            event_history=[],
            metadata={
                "scenario_title": self.scenario.title,
                "origin_country": self.scenario.origin_country,
                "max_ticks": self.max_ticks,
            },
        )

    def _seed_initial_events(self) -> None:
        """
        Schedules the root crisis trigger event at tick 0.
        """
        initial_event = SimulationEvent(
            event_id=f"trigger_{self.scenario.id}_0",
            tick=0,
            priority=1,
            event_type="CRISIS_TRIGGERED",
            source="system",
            affected_countries=self.scenario.affected_countries,
            description=f"Crisis Triggered: {self.scenario.title}. {self.scenario.description}",
            payload={"origin_country": self.scenario.origin_country},
        )
        self.event_queue.schedule(initial_event)

    # ── Lifecycle Controls ────────────────────────────────────────────────────

    def start(self) -> SimulationState:
        """
        Transitions state to RUNNING.
        """
        if self.state.status == "COMPLETED":
            raise ValueError(f"Simulation {self.simulation_id} is already completed")
        self.state.status = "RUNNING"
        return self.state

    def pause(self) -> SimulationState:
        """
        Pauses a running simulation.
        """
        if self.state.status != "RUNNING":
            raise ValueError(f"Cannot pause simulation with status '{self.state.status}'")
        self.state.status = "PAUSED"
        return self.state

    def resume(self) -> SimulationState:
        """
        Resumes a paused simulation.
        """
        if self.state.status != "PAUSED":
            raise ValueError(f"Cannot resume simulation with status '{self.state.status}'")
        self.state.status = "RUNNING"
        return self.state

    # ── Execution Logic ───────────────────────────────────────────────────────

    def step(self) -> SimulationStepResponse:
        """
        Executes a single deterministic simulation step:
        1. If CREATED, marks RUNNING.
        2. Pops all events ready for current_tick.
        3. If no ready events exist and queue is not empty, advances clock to next scheduled event tick.
        4. Processes popped events through EventProcessor, recording history and updating state.
        5. Advances tick by 1 if ready events were processed.
        6. Checks termination conditions.
        """
        if self.state.status == "COMPLETED":
            raise ValueError(f"Cannot step: Simulation {self.simulation_id} is already completed")
        if self.state.status == "PAUSED":
            raise ValueError(f"Cannot step: Simulation {self.simulation_id} is paused")

        if self.state.status == "CREATED":
            self.state.status = "RUNNING"

        current_tick = self.clock.current_tick

        # Check termination safeguard
        if current_tick >= self.max_ticks:
            self.state.status = "COMPLETED"
            return SimulationStepResponse(
                simulation_id=self.simulation_id,
                status=self.state.status,
                current_tick=self.clock.current_tick,
                current_time=self.clock.current_time,
                processed_events_count=0,
                events=[],
                is_completed=True,
            )

        processed_this_step: List[SimulationEvent] = []

        while True:
            ready_events = self.event_queue.pop_ready(current_tick)
            if not ready_events:
                # If nothing processed yet and queue not empty, fast-forward to next event
                if not processed_this_step and not self.event_queue.is_empty():
                    next_event = self.event_queue.peek()
                    if next_event:
                        jump_tick = min(next_event.tick, self.max_ticks)
                        self.clock.set_tick(jump_tick)
                        current_tick = jump_tick
                        continue
                break

            for event in ready_events:
                self.event_processor.process_event(event, self.state)
                self.state.event_history.append(event)
                processed_this_step.append(event)

        self.state.active_events = processed_this_step

        # Advance tick if not completed
        if self.state.status != "COMPLETED":
            self.clock.advance(1)
            self.state.current_tick = self.clock.current_tick
            self.state.current_time = self.clock.current_time

        # Check if completed
        if self.event_queue.is_empty() or self.clock.current_tick >= self.max_ticks:
            self.state.status = "COMPLETED"

        return SimulationStepResponse(
            simulation_id=self.simulation_id,
            status=self.state.status,
            current_tick=self.state.current_tick,
            current_time=self.state.current_time,
            processed_events_count=len(processed_this_step),
            events=processed_this_step,
            is_completed=(self.state.status == "COMPLETED"),
        )

    def run_until_complete(self, max_ticks: Optional[int] = None) -> SimulationState:
        """
        Repeatedly steps the simulation until COMPLETED or loop safeguard reached.
        """
        limit = max_ticks or self.max_ticks
        steps_taken = 0

        if self.state.status == "CREATED":
            self.start()

        while self.state.status == "RUNNING" and self.clock.current_tick < limit:
            step_result = self.step()
            steps_taken += 1
            if step_result.is_completed:
                break

        self.state.status = "COMPLETED"
        return self.state

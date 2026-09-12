"""
Comprehensive Tests for Phase 3: Simulation Engine & Event Clock.
- Virtual Event Clock deterministic operations
- Event Queue multi-attribute priority ordering
- Simulation State initialization and transitions
- Information asymmetry and strictly sequential country progression (Unaware -> Investigating -> Notified -> Coordinating)
- Deterministic placeholder decisions (zero LLM dependency)
- Complete simulation execution across all 3 Phase 2 scenarios
- Exact reproducibility across multiple identical runs
- Error handling and boundary conditions
- REST API endpoint verification
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.schemas.simulation_models import (
    SimulationEvent,
    SimulationState,
    SimulationStepResponse,
)
from app.services.simulation.clock import SimulationClock
from app.services.simulation.decision_maker import DeterministicDecisionMaker
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.event_queue import EventQueue
from app.services.simulation.repository import default_simulation_repository


# ── Clock Tests ───────────────────────────────────────────────────────────────

def test_simulation_clock_advance_and_reset():
    clock = SimulationClock()
    assert clock.current_tick == 0
    assert clock.current_time == "T+00"

    clock.advance(1)
    assert clock.current_tick == 1
    assert clock.current_time == "T+01"

    clock.advance(14)
    assert clock.current_tick == 15
    assert clock.current_time == "T+15"

    clock.reset()
    assert clock.current_tick == 0
    assert clock.current_time == "T+00"


def test_simulation_clock_invalid_advance():
    clock = SimulationClock()
    with pytest.raises(ValueError):
        clock.advance(0)
    with pytest.raises(ValueError):
        clock.advance(-5)


# ── Event Queue Tests ─────────────────────────────────────────────────────────

def test_event_queue_priority_ordering():
    queue = EventQueue()

    e1 = SimulationEvent(
        event_id="e_tick5_low",
        tick=5,
        priority=10,
        event_type="TIMELINE_EVENT",
        description="Tick 5 low priority",
    )
    e2 = SimulationEvent(
        event_id="e_tick5_high",
        tick=5,
        priority=1,
        event_type="TIMELINE_EVENT",
        description="Tick 5 high priority",
    )
    e3 = SimulationEvent(
        event_id="e_tick2",
        tick=2,
        priority=5,
        event_type="CRISIS_TRIGGERED",
        description="Tick 2 event",
    )

    queue.schedule(e1)
    queue.schedule(e2)
    queue.schedule(e3)

    assert len(queue) == 3

    # Tick 2 should pop first regardless of insertion order
    ready_tick_2 = queue.pop_ready(2)
    assert len(ready_tick_2) == 1
    assert ready_tick_2[0].event_id == "e_tick2"

    # Pop ready at tick 5: e2 (priority 1) before e1 (priority 10)
    ready_tick_5 = queue.pop_ready(5)
    assert len(ready_tick_5) == 2
    assert ready_tick_5[0].event_id == "e_tick5_high"
    assert ready_tick_5[1].event_id == "e_tick5_low"

    assert queue.is_empty()


# ── Simulation Creation & State Tests ─────────────────────────────────────────

def test_simulation_creation_scenario_01():
    engine = SimulationEngine.create("scenario_01", mode="coordinated")
    state = engine.state

    assert state.simulation_id.startswith("sim_")
    assert state.scenario_id == "scenario_01"
    assert state.status == "CREATED"
    assert state.current_tick == 0
    assert state.current_time == "T+00"
    assert state.crisis_state.phase == "DETECTION"
    assert len(state.countries) == 15

    # Origin country should initially be Unaware prior to first step
    origin_state = state.countries[state.crisis_state.origin_country]
    assert origin_state.status == "Unaware"
    assert origin_state.aware is False

    # Event queue should contain the initial trigger event
    assert not engine.event_queue.is_empty()
    assert engine.event_queue.peek().event_type == "CRISIS_TRIGGERED"


# ── State Machine & Sequential Status Progression ─────────────────────────────

def test_sequential_country_status_progression():
    """
    Verifies that a country strictly follows:
    Unaware -> Investigating -> Notified -> Coordinating
    with no skipped states.
    """
    engine = SimulationEngine.create("scenario_01")
    origin_id = engine.scenario.origin_country

    assert engine.state.countries[origin_id].status == "Unaware"

    # Step 1 (processes CRISIS_TRIGGERED at T+0)
    # Origin country transitions Unaware -> Investigating
    engine.step()
    assert engine.state.countries[origin_id].status == "Investigating"
    assert engine.state.countries[origin_id].aware is True

    # Step 2 (processes COUNTRY_NOTIFICATION for origin at T+1)
    # Origin country transitions Investigating -> Notified
    engine.step()
    assert engine.state.countries[origin_id].status == "Notified"

    # Step 3 (processes DECISION_REQUIRED + POLICY_ACTION at T+2)
    # Origin country transitions Notified -> Coordinating
    engine.step()
    assert engine.state.countries[origin_id].status == "Coordinating"
    assert engine.state.countries[origin_id].current_action is not None
    assert len(engine.state.decisions) >= 1


def test_information_delay_gating():
    """
    Verifies that countries with information delays do NOT become aware
    until their scheduled delay tick.
    """
    engine = SimulationEngine.create("scenario_01")
    delays = engine.scenario.information_delay

    # Country with a later delay (e.g. country_03 with delay=15)
    delayed_cid = "country_03"
    delay_val = delays[delayed_cid]
    assert delay_val >= 10

    # Step through ticks before delay
    for _ in range(5):
        engine.step()
        if engine.clock.current_tick < delay_val:
            assert engine.state.countries[delayed_cid].status == "Unaware"
            assert engine.state.countries[delayed_cid].aware is False


# ── Decision Maker Tests (Zero LLM) ───────────────────────────────────────────

def test_deterministic_placeholder_decisions_recorded():
    engine = SimulationEngine.create("scenario_01")
    # Step until decisions are recorded
    for _ in range(6):
        engine.step()

    assert len(engine.state.decisions) >= 1
    for dec in engine.state.decisions:
        assert dec.source in ("llm_agent", "deterministic_placeholder", "deterministic_fallback")
        assert dec.action_id in [a.id for a in engine.scenario.available_actions]
        assert len(dec.reasoning) > 20
        assert dec.simulation_id == engine.simulation_id


# ── Full Execution & Completion across All Scenarios ──────────────────────────

def test_full_run_scenario_01_completes():
    engine = SimulationEngine.create("scenario_01", max_ticks=80)
    final_state = engine.run_until_complete()

    assert final_state.status == "COMPLETED"
    assert final_state.current_tick > 20
    assert len(final_state.event_history) > 10
    assert len(final_state.decisions) > 5
    assert final_state.crisis_state.phase in ["RESOLUTION", "RESOLVED"]


def test_full_run_scenario_02_completes():
    engine = SimulationEngine.create("scenario_02", max_ticks=80)
    final_state = engine.run_until_complete()

    assert final_state.status == "COMPLETED"
    assert len(final_state.event_history) > 5
    assert len(final_state.decisions) >= 1


def test_full_run_scenario_03_completes():
    engine = SimulationEngine.create("scenario_03", max_ticks=80)
    final_state = engine.run_until_complete()

    assert final_state.status == "COMPLETED"
    assert len(final_state.event_history) > 5
    assert len(final_state.decisions) >= 1


# ── Reproducibility Tests ─────────────────────────────────────────────────────

def test_deterministic_reproducibility():
    """
    Two separate runs of the same scenario must produce the exact same
    sequence of events, decisions, and country final statuses.
    """
    engine_1 = SimulationEngine.create("scenario_01", max_ticks=50, simulation_id="sim_run_1")
    engine_2 = SimulationEngine.create("scenario_01", max_ticks=50, simulation_id="sim_run_2")

    state_1 = engine_1.run_until_complete()
    state_2 = engine_2.run_until_complete()

    assert state_1.current_tick == state_2.current_tick
    assert len(state_1.event_history) == len(state_2.event_history)

    # Descriptions must match 1:1
    events_1 = [e.description for e in state_1.event_history]
    events_2 = [e.description for e in state_2.event_history]
    assert events_1 == events_2

    # Decision actions must match 1:1
    decisions_1 = [(d.country_id, d.action_id) for d in state_1.decisions]
    decisions_2 = [(d.country_id, d.action_id) for d in state_2.decisions]
    assert decisions_1 == decisions_2

    # Country states must match 1:1
    for cid in state_1.countries:
        assert state_1.countries[cid].status == state_2.countries[cid].status
        assert state_1.countries[cid].current_action == state_2.countries[cid].current_action


# ── Failure & Guard Tests ─────────────────────────────────────────────────────

def test_invalid_scenario_id():
    with pytest.raises(KeyError):
        SimulationEngine.create("nonexistent_scenario_999")


def test_stepping_completed_simulation_raises_error():
    engine = SimulationEngine.create("scenario_01", max_ticks=5)
    engine.run_until_complete()
    assert engine.state.status == "COMPLETED"

    with pytest.raises(ValueError):
        engine.step()


def test_pause_and_resume_controls():
    engine = SimulationEngine.create("scenario_01")
    engine.start()
    assert engine.state.status == "RUNNING"

    engine.pause()
    assert engine.state.status == "PAUSED"

    with pytest.raises(ValueError):
        engine.step()

    engine.resume()
    assert engine.state.status == "RUNNING"
    step_res = engine.step()
    assert step_res.status == "RUNNING"


# ── REST API Endpoint Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_simulation_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create
        create_res = await ac.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "coordinated"})
        assert create_res.status_code == 201
        sim_data = create_res.json()
        sim_id = sim_data["simulation_id"]
        assert sim_data["status"] == "CREATED"

        # 2. Get State
        get_res = await ac.get(f"/api/simulations/{sim_id}")
        assert get_res.status_code == 200
        assert get_res.json()["simulation_id"] == sim_id

        # 3. Step
        step_res = await ac.post(f"/api/simulations/{sim_id}/step")
        assert step_res.status_code == 200
        step_data = step_res.json()
        assert step_data["current_tick"] >= 0

        # 4. Run until complete
        run_res = await ac.post(f"/api/simulations/{sim_id}/run")
        assert run_res.status_code == 200
        assert run_res.json()["status"] == "COMPLETED"

        # 5. Get Events
        events_res = await ac.get(f"/api/simulations/{sim_id}/events")
        assert events_res.status_code == 200
        events = events_res.json()
        assert len(events) > 5


@pytest.mark.asyncio
async def test_api_simulation_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/simulations/unknown_sim_xyz")
        assert res.status_code == 404

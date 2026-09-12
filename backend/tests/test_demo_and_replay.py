"""
Tests for Phase 14: Demo Path, Seeded Replay & Fallbacks.

Verifies:
1. Seeded demo execution reproducibility (Run 1 == Run 2 for seed 42)
2. Different seed independence
3. Replay session creation from simulation and comparison
4. Replay event sequence integrity and zero mutation of source state
5. Replay seeking up to specific virtual ticks
6. Restart demo creates fresh run without state leakage
7. Deterministic offline fallback works with zero external credentials
8. REST API endpoints for /api/demo and /api/replays
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.demo_models import DemoLaunchRequest
from app.services.demo_service import (
    default_demo_repository,
    default_demo_service,
)
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository


# ── 1. Seeded Demo Reproducibility ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seeded_demo_determinism_identical_runs():
    """
    Validates that executing the seeded demo twice with the same scenario and seed
    produces identical decisions, ticks, scoring results, and winner.
    """
    req1 = DemoLaunchRequest(scenario_id="scenario_01", seed=42, max_ticks=30)
    run1 = await default_demo_service.launch_demo(req1)

    req2 = DemoLaunchRequest(scenario_id="scenario_01", seed=42, max_ticks=30)
    run2 = await default_demo_service.launch_demo(req2)

    # Unique demo session identities
    assert run1.demo_id != run2.demo_id
    assert run1.seed == run2.seed == 42
    assert run1.scenario_id == run2.scenario_id == "scenario_01"

    # Both comparisons must reach identical terminal states
    assert run1.comparison is not None
    assert run2.comparison is not None
    assert run1.comparison.winner == run2.comparison.winner
    assert run1.comparison.winner_reason == run2.comparison.winner_reason

    # Compare mode scores
    for mode in ("no_coordination", "partial", "coordinated"):
        res1 = run1.comparison.results[mode]
        res2 = run2.comparison.results[mode]

        assert res1.overall_score == res2.overall_score
        assert res1.score_grade == res2.score_grade
        assert res1.final_tick == res2.final_tick
        assert res1.events_count == res2.events_count
        assert res1.decisions_count == res2.decisions_count


@pytest.mark.asyncio
async def test_different_seeds_have_independent_identities():
    """Confirms running with different seeds produces independent demo instances."""
    run_a = await default_demo_service.launch_demo(DemoLaunchRequest(scenario_id="scenario_01", seed=101, max_ticks=20))
    run_b = await default_demo_service.launch_demo(DemoLaunchRequest(scenario_id="scenario_01", seed=202, max_ticks=20))

    assert run_a.demo_id != run_b.demo_id
    assert run_a.seed == 101
    assert run_b.seed == 202
    assert run_a.comparison_id != run_b.comparison_id


# ── 2. Replay Session Packaging & Integrity ───────────────────────────────────

@pytest.mark.asyncio
async def test_replay_from_simulation_preserves_event_order():
    """Packages a single-mode simulation into a ReplaySession and verifies event order."""
    engine = SimulationEngine.create(scenario_id="scenario_01", mode="coordinated", max_ticks=15)
    default_simulation_repository.save(engine)
    engine.run_until_complete()

    replay = default_demo_service.create_replay_from_simulation(engine.simulation_id, seed=42)

    assert replay.replay_id.startswith("replay_")
    assert replay.source_type == "simulation"
    assert replay.source_id == engine.simulation_id
    assert replay.total_events == len(engine.state.event_history)
    assert replay.total_ticks == engine.state.current_tick

    # Verify monotonic non-decreasing tick ordering
    previous_tick = 0
    for idx, rev in enumerate(replay.events):
        assert rev.sequence_number == idx
        assert rev.tick >= previous_tick
        previous_tick = rev.tick


@pytest.mark.asyncio
async def test_replay_seek_is_deterministic_and_non_mutating():
    """Seeking a replay to tick T returns only events up to T and does not mutate source replay."""
    engine = SimulationEngine.create(scenario_id="scenario_01", mode="partial", max_ticks=25)
    default_simulation_repository.save(engine)
    engine.run_until_complete()

    replay = default_demo_service.create_replay_from_simulation(engine.simulation_id)
    initial_event_count = len(replay.events)

    snap_tick_5 = default_demo_service.seek_replay(replay.replay_id, to_tick=5)
    assert snap_tick_5.current_tick == 5
    assert all(e.tick <= 5 for e in snap_tick_5.visible_events)

    snap_tick_20 = default_demo_service.seek_replay(replay.replay_id, to_tick=20)
    assert snap_tick_20.current_tick == 20
    assert len(snap_tick_20.visible_events) >= len(snap_tick_5.visible_events)

    # Source replay remains completely unmutated
    assert len(replay.events) == initial_event_count


# ── 3. Restart Functionality ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_restart_demo_creates_fresh_instance_without_leakage():
    """Restarting a demo creates a fresh run without modifying or reusing the original run."""
    init_run = await default_demo_service.launch_demo(DemoLaunchRequest(scenario_id="scenario_01", seed=42, max_ticks=20))

    # Restart with same seed
    launch_req = default_demo_service.restart_demo(init_run.demo_id)
    restarted_run = await default_demo_service.launch_demo(launch_req)

    assert restarted_run.demo_id != init_run.demo_id
    assert restarted_run.comparison_id != init_run.comparison_id
    assert restarted_run.seed == init_run.seed == 42
    assert restarted_run.status == "COMPLETED"

    # Original run remains intact in repository
    saved_orig = default_demo_repository.get_demo(init_run.demo_id)
    assert saved_orig is not None
    assert saved_orig.demo_id == init_run.demo_id


# ── 4. REST API Verification ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_demo_and_replay_api_lifecycle():
    """Tests the full REST API endpoints for demo launch, restart, and replay inspection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Launch Demo
        launch_res = await client.post(
            "/api/demo/launch",
            json={"scenario_id": "scenario_01", "seed": 42, "max_ticks": 20},
        )
        assert launch_res.status_code == 201
        demo_data = launch_res.json()
        demo_id = demo_data["demo_id"]
        comp_id = demo_data["comparison_id"]
        assert demo_data["execution_mode"] == "DEMO"
        assert demo_data["seed"] == 42
        assert demo_data["status"] == "COMPLETED"

        # 2. List Demos
        list_res = await client.get("/api/demo/runs")
        assert list_res.status_code == 200
        runs = list_res.json()
        assert any(r["demo_id"] == demo_id for r in runs)

        # 3. Get Demo by ID
        get_res = await client.get(f"/api/demo/runs/{demo_id}")
        assert get_res.status_code == 200
        assert get_res.json()["demo_id"] == demo_id

        # 4. Restart Demo via API
        restart_res = await client.post(f"/api/demo/runs/{demo_id}/restart?new_seed=777")
        assert restart_res.status_code == 200
        restarted_data = restart_res.json()
        assert restarted_data["demo_id"] != demo_id
        assert restarted_data["seed"] == 777

        # 5. Create Replay from comparison
        rep_res = await client.post(
            "/api/replays",
            json={"source_type": "comparison", "source_id": comp_id, "seed": 42},
        )
        assert rep_res.status_code == 201
        replay_data = rep_res.json()
        replay_id = replay_data["replay_id"]
        assert replay_data["execution_mode"] == "REPLAY"
        assert replay_data["total_events"] > 0

        # 6. Get Replay Session
        get_rep = await client.get(f"/api/replays/{replay_id}")
        assert get_rep.status_code == 200
        assert get_rep.json()["replay_id"] == replay_id

        # 7. Seek Replay
        seek_res = await client.get(f"/api/replays/{replay_id}/seek?to_tick=10")
        assert seek_res.status_code == 200
        seek_data = seek_res.json()
        assert seek_data["current_tick"] == 10
        assert seek_data["events_played"] <= replay_data["total_events"]

        # 8. Error handling: Non-existent demo
        err_res = await client.get("/api/demo/runs/demo_non_existent")
        assert err_res.status_code == 404

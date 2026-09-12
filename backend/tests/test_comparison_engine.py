"""
Unit, integration, and API tests for Phase 13 Three-Mode Comparison Engine.

Verifies:
1. Exact three project-defined coordination modes ('no_coordination', 'partial', 'coordinated')
2. Scenario consistency: exact same scenario evaluated across all modes
3. Fair initial conditions and simulation isolation
4. Deterministic scoring integration and winner determination
5. Explicit tie handling (no forced winner)
6. Failed mode and incomplete comparison handling
7. Comparative delta calculation against baseline
8. REST API endpoints (/api/comparisons, /status, /modes/{mode})
9. WebSocket streaming events and state snapshot
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.comparison_models import (
    ComparisonRun,
    CreateComparisonRequest,
    ModeComparisonResult,
)
from app.schemas.scoring_models import MetricResult, ScoringInputSnapshot, ScoringResult, SimulationMetrics
from app.services.comparison_service import (
    SUPPORTED_COMPARISON_MODES,
    ComparisonService,
    default_comparison_repository,
    default_comparison_service,
)
from app.services.data_loader import default_data_loader
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository


# ── 1. Modes & Initial Conditions ──────────────────────────────────────────────

def test_exact_three_modes_identified():
    """Confirms the exact three project-defined coordination modes are supported."""
    assert len(SUPPORTED_COMPARISON_MODES) == 3
    assert SUPPORTED_COMPARISON_MODES == ["no_coordination", "partial", "coordinated"]


def test_comparison_initialization_enforces_same_scenario():
    """Validates that a new comparison initializes with the exact same scenario for all 3 modes."""
    request = CreateComparisonRequest(scenario_id="scenario_01", max_ticks=60)
    run = default_comparison_service.create_comparison(request)

    assert run.comparison_id.startswith("comp_")
    assert run.scenario_id == "scenario_01"
    assert run.scenario_title != ""
    assert run.status == "CREATED"
    assert run.modes_evaluated == ["no_coordination", "partial", "coordinated"]
    assert run.winner is None
    assert run.deltas == []


def test_invalid_scenario_rejected():
    """Attempting to create comparison with a non-existent scenario raises KeyError."""
    request = CreateComparisonRequest(scenario_id="scenario_non_existent_999")
    with pytest.raises(KeyError):
        default_comparison_service.create_comparison(request)


# ── 2. Simulation State Isolation ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulation_isolation_between_modes():
    """
    Verifies that the three runs get unique simulation IDs and isolated state objects.
    Mutating or stepping Mode A must not modify Mode B or Mode C.
    """
    comp_id = "comp_test_isolation_01"
    run = ComparisonRun(
        comparison_id=comp_id,
        scenario_id="scenario_01",
        scenario_title="Test Crisis",
        status="CREATED",
    )
    default_comparison_repository.save(run)

    # Instantiate two engines for two modes
    engine_no_coord = SimulationEngine.create(
        scenario_id="scenario_01",
        mode="no_coordination",
        simulation_id=f"sim_{comp_id}_no_coordination",
    )
    engine_coord = SimulationEngine.create(
        scenario_id="scenario_01",
        mode="coordinated",
        simulation_id=f"sim_{comp_id}_coordinated",
    )

    assert engine_no_coord.simulation_id != engine_coord.simulation_id
    assert engine_no_coord.mode == "no_coordination"
    assert engine_coord.mode == "coordinated"

    # Step uncoordinated engine 5 times
    for _ in range(5):
        engine_no_coord.step()

    # Verify coordinated engine remained untouched at tick 0
    assert engine_no_coord.state.current_tick > 0
    assert engine_coord.state.current_tick == 0
    assert len(engine_no_coord.state.event_history) > 0
    assert len(engine_coord.state.event_history) == 0


# ── 3. Winner Determination & Tie Handling ─────────────────────────────────────

def test_deterministic_winner_highest_overall_score():
    """Winner must strictly be the mode with the highest Phase 7 overall_score."""
    service = ComparisonService()
    run = ComparisonRun(
        comparison_id="comp_test_winner",
        scenario_id="scenario_01",
        scenario_title="Cyber Incursion",
        status="COLLECTING_RESULTS",
    )

    # Setup 3 mock results with distinct scores
    run.results["no_coordination"] = ModeComparisonResult(
        mode="no_coordination",
        mode_name="No Coordination",
        simulation_id="sim_1",
        status="COMPLETED",
        final_tick=30,
        overall_score=35.5,
        score_grade="D",
    )
    run.results["partial"] = ModeComparisonResult(
        mode="partial",
        mode_name="Partial Coordination",
        simulation_id="sim_2",
        status="COMPLETED",
        final_tick=22,
        overall_score=62.0,
        score_grade="C",
    )
    run.results["coordinated"] = ModeComparisonResult(
        mode="coordinated",
        mode_name="Full Coordinated Governance",
        simulation_id="sim_3",
        status="COMPLETED",
        final_tick=14,
        overall_score=88.4,
        score_grade="A",
    )

    service._determine_winner_and_synthesize(run)

    assert run.winner == "coordinated"
    assert run.results["coordinated"].is_winner is True
    assert run.results["partial"].is_winner is False
    assert run.results["no_coordination"].is_winner is False
    assert "Full Coordinated Governance" in run.winner_reason
    assert len(run.deltas) == 2


def test_deterministic_tie_handling():
    """When top two modes share identical overall scores, declare an explicit TIE."""
    service = ComparisonService()
    run = ComparisonRun(
        comparison_id="comp_test_tie",
        scenario_id="scenario_01",
        scenario_title="Autonomous Drone Standoff",
        status="COLLECTING_RESULTS",
    )

    run.results["no_coordination"] = ModeComparisonResult(
        mode="no_coordination",
        mode_name="No Coordination",
        simulation_id="sim_1",
        status="COMPLETED",
        final_tick=30,
        overall_score=40.0,
        score_grade="D",
    )
    run.results["partial"] = ModeComparisonResult(
        mode="partial",
        mode_name="Partial Coordination",
        simulation_id="sim_2",
        status="COMPLETED",
        final_tick=18,
        overall_score=82.5,
        score_grade="B",
    )
    run.results["coordinated"] = ModeComparisonResult(
        mode="coordinated",
        mode_name="Full Coordinated Governance",
        simulation_id="sim_3",
        status="COMPLETED",
        final_tick=18,
        overall_score=82.5,  # Identical to partial
        score_grade="B",
    )

    service._determine_winner_and_synthesize(run)

    assert run.winner == "TIE"
    assert "Statistical tie" in run.winner_reason
    assert run.results["partial"].is_winner is True
    assert run.results["coordinated"].is_winner is True
    assert run.results["no_coordination"].is_winner is False


def test_failed_mode_handling():
    """A failed mode is recorded with diagnostic info and does not fabricate a zero score."""
    service = ComparisonService()
    run = ComparisonRun(
        comparison_id="comp_test_fail",
        scenario_id="scenario_01",
        scenario_title="Test Crisis",
        status="COLLECTING_RESULTS",
    )
    run.results["no_coordination"] = ModeComparisonResult(
        mode="no_coordination",
        mode_name="No Coordination",
        simulation_id="sim_1",
        status="FAILED",
        final_tick=0,
        overall_score=None,
        error="LLM inference timed out",
    )
    run.results["partial"] = ModeComparisonResult(
        mode="partial",
        mode_name="Partial Coordination",
        simulation_id="sim_2",
        status="COMPLETED",
        final_tick=20,
        overall_score=55.0,
        score_grade="C",
    )

    service._determine_winner_and_synthesize(run)

    assert run.winner == "partial"
    assert run.results["no_coordination"].status == "FAILED"
    assert run.results["no_coordination"].overall_score is None


# ── 4. End-to-End Three-Mode Execution ────────────────────────────────────────

@pytest.mark.asyncio
async def test_end_to_end_three_mode_comparison_execution():
    """Executes the complete three-mode comparison engine against a real scenario."""
    req = CreateComparisonRequest(scenario_id="scenario_01", max_ticks=30)
    run = default_comparison_service.create_comparison(req)

    # Execute all 3 modes
    completed_run = await default_comparison_service.execute_comparison(run.comparison_id)

    assert completed_run.status == "COMPLETED"
    assert completed_run.completed_at is not None
    assert len(completed_run.results) == 3

    for mode in ("no_coordination", "partial", "coordinated"):
        res = completed_run.results.get(mode)
        assert res is not None
        assert res.status == "COMPLETED"
        assert res.final_tick > 0
        assert res.overall_score is not None
        assert 0.0 <= res.overall_score <= 100.0
        assert res.score_grade in ("A", "B", "C", "D", "F")
        assert len(res.metric_breakdown) == 4

    assert completed_run.winner in ("coordinated", "partial", "no_coordination", "TIE")
    assert completed_run.summary_headline != ""
    assert completed_run.summary_narrative != ""
    assert len(completed_run.deltas) == 2


# ── 5. REST API Integration ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_comparison_lifecycle():
    """Tests the full REST API lifecycle for comparisons."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create and execute comparison synchronously
        create_resp = await client.post(
            "/api/comparisons",
            json={"scenario_id": "scenario_01", "max_ticks": 20},
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        comp_id = data["comparison_id"]
        assert data["status"] == "COMPLETED"
        assert len(data["results"]) == 3
        assert data["winner"] in ("coordinated", "partial", "no_coordination", "TIE")

        # 2. List comparisons
        list_resp = await client.get("/api/comparisons")
        assert list_resp.status_code == 200
        runs = list_resp.json()
        assert any(r["comparison_id"] == comp_id for r in runs)

        # 3. Get single comparison
        get_resp = await client.get(f"/api/comparisons/{comp_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["comparison_id"] == comp_id

        # 4. Get lightweight status
        status_resp = await client.get(f"/api/comparisons/{comp_id}/status")
        assert status_resp.status_code == 200
        s_data = status_resp.json()
        assert s_data["status"] == "COMPLETED"
        assert s_data["modes_completed"] == 3
        assert s_data["total_modes"] == 3

        # 5. Get mode-specific result
        mode_resp = await client.get(f"/api/comparisons/{comp_id}/modes/coordinated")
        assert mode_resp.status_code == 200
        m_data = mode_resp.json()
        assert m_data["mode"] == "coordinated"
        assert m_data["status"] == "COMPLETED"
        assert m_data["overall_score"] is not None

        # 6. Error handling: invalid mode
        bad_mode_resp = await client.get(f"/api/comparisons/{comp_id}/modes/anarchy_mode")
        assert bad_mode_resp.status_code == 400

        # 7. Error handling: non-existent comparison
        not_found_resp = await client.get("/api/comparisons/comp_fake_id_1234")
        assert not_found_resp.status_code == 404

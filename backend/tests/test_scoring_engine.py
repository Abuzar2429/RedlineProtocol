"""
Phase 7 — Deterministic Scoring Engine Comprehensive Test Suite.

Verifies:
1. Individual pure metric calculations (Risk, Response Time, Coordination, Unresolved Issues)
2. Boundary, zero, and edge-case handling (division by zero, duplicate actions, over-clamping)
3. Weight summation and overall composite score calculation
4. Deterministic replay reproducibility
5. Three-mode comparative scoring (no_coordination, partial, coordinated)
6. Simulation state snapshot extraction and end-to-end integration
7. REST API endpoints (/score, /metrics, /score/breakdown)
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.scoring_models import MetricResult, ScoringInputSnapshot, ScoringResult, SimulationMetrics
from app.scoring import (
    BENCHMARK_RESPONSE_TICKS,
    DEFAULT_ACTION_RISK_REDUCTIONS,
    DEFAULT_TOTAL_COUNTRIES,
    INITIAL_RISK,
    METRIC_WEIGHTS,
    SCORING_FORMULA_VERSION,
    compute_coordination_score,
    compute_overall_score,
    compute_response_time,
    compute_risk_score,
    default_scoring_engine,
    default_scoring_repository,
    extract_and_score_unresolved_issues,
)
from app.scoring.snapshot import ScoringSnapshotBuilder
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository


# ── 1. Pure Metric Unit Tests ──────────────────────────────────────────────────

def test_weights_sum_to_one():
    """Validates that spec-defined weights sum exactly to 1.0 (100%)."""
    total_weight = sum(METRIC_WEIGHTS.values())
    assert pytest.approx(total_weight, 0.0001) == 1.0
    assert METRIC_WEIGHTS["risk_reduction"] == 0.25
    assert METRIC_WEIGHTS["response_time"] == 0.25
    assert METRIC_WEIGHTS["coordination"] == 0.25
    assert METRIC_WEIGHTS["unresolved_issues"] == 0.25


def test_metric_1_risk_score_baseline_zero_actions():
    """When no actions are taken and coordination is 0, risk stays at 100 and reduction is 0%."""
    risk_final, reduction_pct, metric = compute_risk_score(
        unique_actions=[],
        coordination_ratio=0.0,
    )
    assert risk_final == 100.0
    assert reduction_pct == 0.0
    assert metric.normalized_score == 0.0
    assert metric.weighted_score == 0.0
    assert metric.display_value == "↓0%"


def test_metric_1_risk_score_action_deductions_and_deduplication():
    """Action deductions apply fixed amounts and do not stack twice for duplicate actions."""
    # suspend_system_temporarily: -30, notify_international: -15 -> sum = -45
    # duplicate suspend_system_temporarily must NOT deduct again
    actions = [
        "suspend_system_temporarily",
        "notify_international",
        "suspend_system_temporarily",  # duplicate
    ]
    risk_final, reduction_pct, metric = compute_risk_score(
        unique_actions=actions,
        coordination_ratio=0.0,
    )
    # Risk before coord = 100 - 45 = 55.0. With coord=0.0 -> risk_final = 55.0
    assert risk_final == 55.0
    assert reduction_pct == 45.0
    assert metric.normalized_score == 45.0
    assert metric.weighted_score == 11.25  # 45 * 0.25


def test_metric_1_risk_score_coordination_multiplier():
    """Higher coordination ratio improves risk reduction via the (1 - 0.2 * coord) multiplier."""
    actions = ["suspend_system_temporarily", "notify_international"]  # -45 deduction -> 55.0
    
    # At coord = 1.0, multiplier = 1 - 0.2 * 1.0 = 0.8
    # risk_final = 55.0 * 0.8 = 44.0
    risk_final, reduction_pct, metric = compute_risk_score(
        unique_actions=actions,
        coordination_ratio=1.0,
    )
    assert risk_final == 44.0
    assert reduction_pct == 56.0


def test_metric_1_risk_score_maximum_clamping():
    """Extreme deductions that exceed 100 are clamped to 0.0 risk and 100% reduction."""
    actions = [
        "suspend_system_temporarily",  # -30
        "ratify_joint_containment",    # -35
        "request_joint_investigation", # -15
        "notify_international",        # -15
        "share_technical_evidence",    # -10
        "issue_public_warning",        # -5
    ]
    # Sum of deductions = -110 -> would be -10 without clamping
    risk_final, reduction_pct, metric = compute_risk_score(
        unique_actions=actions,
        coordination_ratio=1.0,
    )
    assert risk_final == 0.0
    assert reduction_pct == 100.0
    assert metric.normalized_score == 100.0
    assert metric.weighted_score == 25.0


def test_metric_2_response_time_rapid_coordinated():
    """Response time computed as coordinated_action_tick - detection_tick."""
    resp_time, metric = compute_response_time(
        detection_tick=0,
        coordinated_action_tick=14,
        final_tick=25,
    )
    assert resp_time == 14
    assert metric.raw_value == 14.0
    assert metric.display_value == "14 min"
    # Benchmark 30 ticks: 100 - (14/30)*100 = 53.33
    assert pytest.approx(metric.normalized_score, 0.1) == 53.33
    assert metric.weighted_score == round(metric.normalized_score * 0.25, 2)


def test_metric_2_response_time_uncoordinated_fallback():
    """When no coordinated action occurred, falls back to final_tick and applies failure penalty."""
    resp_time, metric = compute_response_time(
        detection_tick=0,
        coordinated_action_tick=None,
        final_tick=31,
    )
    assert resp_time == 31
    assert metric.display_value == "31 min (uncoordinated)"
    # Penalized normalized score (max 30 points)
    assert metric.normalized_score < 30.0


def test_metric_3_coordination_score_normal():
    """Coordination ratio is approving_countries / total_countries."""
    # 11 agreed out of 15 invited (rules.md §5.3 example)
    ratio, metric = compute_coordination_score(approving_count=11, total_countries=15)
    assert pytest.approx(ratio, 0.001) == 0.7333
    assert metric.display_value == "11/15"
    assert pytest.approx(metric.normalized_score, 0.1) == 73.33
    assert metric.weighted_score == round(metric.normalized_score * 0.25, 2)


def test_metric_3_coordination_score_zero_and_all():
    """Tests 0 approving and all 15 approving."""
    zero_ratio, zero_metric = compute_coordination_score(approving_count=0, total_countries=15)
    assert zero_ratio == 0.0
    assert zero_metric.normalized_score == 0.0

    all_ratio, all_metric = compute_coordination_score(approving_count=15, total_countries=15)
    assert all_ratio == 1.0
    assert all_metric.normalized_score == 100.0


def test_metric_3_coordination_score_division_by_zero_safe():
    """Total countries <= 0 is safely handled without ZeroDivisionError."""
    ratio, metric = compute_coordination_score(approving_count=5, total_countries=0)
    assert ratio == 0.0
    assert metric.normalized_score == 0.0


def test_metric_4_unresolved_issues_zero():
    """Zero unresolved issues yields maximum score of 100.0."""
    issues, count, metric = extract_and_score_unresolved_issues(
        unresolved_issues_raw=[],
        negotiation_rounds_count=1,
    )
    assert issues == []
    assert count == 0
    assert metric.normalized_score == 100.0
    assert metric.weighted_score == 25.0
    assert metric.display_value == "0 unresolved"


def test_metric_4_unresolved_issues_deduplication_and_penalty():
    """Deduplicates raw issues and applies 20 points deduction per distinct issue."""
    raw_issues = [
        "Data-sharing restrictions",
        "Liability",
        "data-sharing restrictions",  # duplicate case-insensitive
        "Attribution",
    ]
    issues, count, metric = extract_and_score_unresolved_issues(
        unresolved_issues_raw=raw_issues,
        negotiation_rounds_count=2,
    )
    assert count == 3
    assert len(issues) == 3
    # 100 - (3 * 20) = 40.0
    assert metric.normalized_score == 40.0
    assert metric.weighted_score == 10.0


def test_metric_4_unresolved_issues_over_clamp():
    """6 or more unresolved issues clamp normalized score to 0.0 (no negative score)."""
    raw_issues = [f"Issue #{i}" for i in range(7)]
    issues, count, metric = extract_and_score_unresolved_issues(
        unresolved_issues_raw=raw_issues,
        negotiation_rounds_count=3,
    )
    assert count == 7
    assert metric.normalized_score == 0.0
    assert metric.weighted_score == 0.0


# ── 2. Composite Overall Score & Grade Tests ──────────────────────────────────

def test_overall_score_perfect_grade_a():
    """All metrics at maximum yield 100.0 overall score and Grade A."""
    perfect_metrics = [
        MetricResult(
            metric_id="risk_reduction", name="Risk Reduction", raw_value=100.0, unit="%",
            display_value="↓100%", normalized_score=100.0, weight=0.25, weighted_score=25.0,
            interpretation="Ideal", evidence={},
        ),
        MetricResult(
            metric_id="response_time", name="Response Time", raw_value=0.0, unit="minutes",
            display_value="0 min", normalized_score=100.0, weight=0.25, weighted_score=25.0,
            interpretation="Ideal", evidence={},
        ),
        MetricResult(
            metric_id="coordination", name="Coordination", raw_value=1.0, unit="ratio",
            display_value="15/15", normalized_score=100.0, weight=0.25, weighted_score=25.0,
            interpretation="Ideal", evidence={},
        ),
        MetricResult(
            metric_id="unresolved_issues", name="Unresolved Issues", raw_value=0.0, unit="count",
            display_value="0 unresolved", normalized_score=100.0, weight=0.25, weighted_score=25.0,
            interpretation="Ideal", evidence={},
        ),
    ]
    overall, grade, headline = compute_overall_score(perfect_metrics)
    assert overall == 100.0
    assert grade == "A"


def test_overall_score_worst_grade_f():
    """All metrics at minimum yield 0.0 overall score and Grade F."""
    worst_metrics = [
        MetricResult(
            metric_id="risk_reduction", name="Risk Reduction", raw_value=0.0, unit="%",
            display_value="↓0%", normalized_score=0.0, weight=0.25, weighted_score=0.0,
            interpretation="Poor", evidence={},
        ),
        MetricResult(
            metric_id="response_time", name="Response Time", raw_value=30.0, unit="minutes",
            display_value="30 min", normalized_score=0.0, weight=0.25, weighted_score=0.0,
            interpretation="Poor", evidence={},
        ),
        MetricResult(
            metric_id="coordination", name="Coordination", raw_value=0.0, unit="ratio",
            display_value="0/15", normalized_score=0.0, weight=0.25, weighted_score=0.0,
            interpretation="Poor", evidence={},
        ),
        MetricResult(
            metric_id="unresolved_issues", name="Unresolved Issues", raw_value=5.0, unit="count",
            display_value="5 unresolved", normalized_score=0.0, weight=0.25, weighted_score=0.0,
            interpretation="Poor", evidence={},
        ),
    ]
    overall, grade, headline = compute_overall_score(worst_metrics)
    assert overall == 0.0
    assert grade == "F"


# ── 3. Deterministic Replay Test ──────────────────────────────────────────────

def test_deterministic_replay_produces_identical_results():
    """Given identical snapshot inputs, scoring engine produces bit-for-bit identical results."""
    snapshot = ScoringInputSnapshot(
        simulation_id="sim_deterministic_test",
        scenario_id="scenario_01",
        mode="coordinated",
        start_tick=0,
        final_tick=25,
        simulation_status="COMPLETED",
        crisis_phase="RESOLVED",
        unique_actions_taken=["suspend_system_temporarily", "notify_international", "share_technical_evidence"],
        action_risk_reductions=DEFAULT_ACTION_RISK_REDUCTIONS,
        detection_tick=0,
        coordinated_action_tick=14,
        coordinated_action_occurred=True,
        total_countries=15,
        participating_countries=[f"country_{i:02d}" for i in range(1, 16)],
        approving_countries=[f"country_{i:02d}" for i in range(1, 12)],  # 11 countries
        opposing_countries=["country_12", "country_13"],
        undecided_countries=["country_14", "country_15"],
        negotiation_sessions_count=1,
        negotiation_rounds_count=2,
        final_agreement_reached=True,
        final_negotiation_status="ACCEPTED",
        unresolved_issues_raw=["Liability", "Attribution"],
    )

    res1 = default_scoring_engine.evaluate_snapshot(snapshot)
    res2 = default_scoring_engine.evaluate_snapshot(snapshot)

    # Core scores
    assert res1.overall_score == res2.overall_score
    assert res1.score_grade == res2.score_grade
    assert res1.performance_headline == res2.performance_headline
    
    # Spec metrics
    assert res1.metrics.risk_final == res2.metrics.risk_final
    assert res1.metrics.risk_reduction_pct == res2.metrics.risk_reduction_pct
    assert res1.metrics.response_time_minutes == res2.metrics.response_time_minutes
    assert res1.metrics.coordination_ratio == res2.metrics.coordination_ratio
    assert res1.metrics.unresolved_issues == res2.metrics.unresolved_issues
    assert res1.metrics.agreement_reached == res2.metrics.agreement_reached

    # Metric breakdown
    for m1, m2 in zip(res1.metric_breakdown, res2.metric_breakdown):
        assert m1.metric_id == m2.metric_id
        assert m1.raw_value == m2.raw_value
        assert m1.normalized_score == m2.normalized_score
        assert m1.weighted_score == m2.weighted_score


# ── 4. Three-Mode Comparative Scoring ─────────────────────────────────────────

def test_three_mode_comparative_scoring():
    """
    Evaluates how the exact same scenario produces distinct governance outcomes
    across the three coordination modes (preparing for Phase 13 comparison).
    """
    # 1. No Coordination
    snap_no_coord = ScoringInputSnapshot(
        simulation_id="sim_compare_no_coord",
        scenario_id="scenario_01",
        mode="no_coordination",
        start_tick=0,
        final_tick=31,
        simulation_status="COMPLETED",
        crisis_phase="RESOLVED",
        unique_actions_taken=["investigate_internally"],
        action_risk_reductions=DEFAULT_ACTION_RISK_REDUCTIONS,
        detection_tick=0,
        coordinated_action_tick=None,
        coordinated_action_occurred=False,
        total_countries=15,
        participating_countries=["country_01", "country_02"],
        approving_countries=[],
        opposing_countries=["country_01", "country_02"],
        undecided_countries=[],
        negotiation_sessions_count=1,
        negotiation_rounds_count=1,
        final_agreement_reached=False,
        final_negotiation_status="FAILED",
        unresolved_issues_raw=["Liability", "Border Controls", "Attribution", "Telemetry Access", "Audit Mandate"],
    )

    # 2. Coordinated Mode
    snap_coord = ScoringInputSnapshot(
        simulation_id="sim_compare_coord",
        scenario_id="scenario_01",
        mode="coordinated",
        start_tick=0,
        final_tick=25,
        simulation_status="COMPLETED",
        crisis_phase="RESOLVED",
        unique_actions_taken=[
            "investigate_internally",
            "notify_affected",
            "suspend_system_temporarily",
            "share_technical_evidence",
            "ratify_joint_containment",
        ],
        action_risk_reductions=DEFAULT_ACTION_RISK_REDUCTIONS,
        detection_tick=0,
        coordinated_action_tick=14,
        coordinated_action_occurred=True,
        total_countries=15,
        participating_countries=[f"country_{i:02d}" for i in range(1, 16)],
        approving_countries=[f"country_{i:02d}" for i in range(1, 14)],  # 13 approving
        opposing_countries=["country_14"],
        undecided_countries=["country_15"],
        negotiation_sessions_count=1,
        negotiation_rounds_count=2,
        final_agreement_reached=True,
        final_negotiation_status="ACCEPTED",
        unresolved_issues_raw=["Liability"],
    )

    score_no_coord = default_scoring_engine.evaluate_snapshot(snap_no_coord)
    score_coord = default_scoring_engine.evaluate_snapshot(snap_coord)

    # Coordinated mode outperforms uncoordinated mode across all metrics:
    # 1. Coordination Ratio
    assert score_coord.metrics.coordination_ratio > score_no_coord.metrics.coordination_ratio
    assert score_no_coord.metrics.coordination_ratio == 0.0

    # 2. Risk Reduction
    assert score_coord.metrics.risk_reduction_pct > score_no_coord.metrics.risk_reduction_pct

    # 3. Response Time (Coordinated resolved in 14 min vs 31 min uncoordinated)
    assert score_coord.metrics.response_time_minutes < score_no_coord.metrics.response_time_minutes

    # 4. Unresolved Issues (1 vs 5)
    assert score_coord.metrics.unresolved_issues_count < score_no_coord.metrics.unresolved_issues_count

    # 5. Overall composite score and grade
    assert score_coord.overall_score > score_no_coord.overall_score
    assert score_coord.score_grade in ("A", "B")
    assert score_no_coord.score_grade in ("D", "F")


# ── 5. End-to-End Simulation Integration ──────────────────────────────────────

def test_full_simulation_engine_scoring_integration():
    """Tests running a real SimulationEngine run and evaluating its outcome with ScoringEngine."""
    engine = SimulationEngine.create(
        scenario_id="scenario_01",
        mode="coordinated",
    )
    default_simulation_repository.save(engine)

    # Step simulation through 12 ticks
    for _ in range(12):
        engine.step()

    # Evaluate live metrics mid-simulation
    live_metrics = default_scoring_engine.evaluate_live_metrics(engine.state)
    assert isinstance(live_metrics, SimulationMetrics)
    assert live_metrics.countries_total == 15
    assert live_metrics.risk_initial == 100.0

    # Trigger coordination and step to complete
    engine.run_until_complete()
    assert engine.state.status in ("COMPLETED", "RUNNING")

    # Evaluate complete state
    scoring_result = default_scoring_engine.evaluate_state(engine.state)
    assert isinstance(scoring_result, ScoringResult)
    assert scoring_result.formula_version == SCORING_FORMULA_VERSION
    assert len(scoring_result.metric_breakdown) == 4
    assert 0.0 <= scoring_result.overall_score <= 100.0
    assert scoring_result.score_grade in ("A", "B", "C", "D", "F")
    assert scoring_result.is_authoritative is True


# ── 6. REST API Endpoints ─────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_api_scoring_lifecycle():
    """Verifies all REST API endpoints for scoring."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Create a simulation
        create_res = await client.post(
            "/api/simulations",
            json={"scenario_id": "scenario_01", "mode": "coordinated"},
        )
        assert create_res.status_code == 201
        sim_data = create_res.json()
        sim_id = sim_data["simulation_id"]

        # 2. Advance 5 steps
        for _ in range(5):
            await client.post(f"/api/simulations/{sim_id}/step")

        # 3. GET live metrics (/metrics)
        metrics_res = await client.get(f"/api/simulations/{sim_id}/metrics")
        assert metrics_res.status_code == 200
        metrics_data = metrics_res.json()
        assert "risk_reduction_pct" in metrics_data
        assert "response_time_minutes" in metrics_data
        assert "coordination_ratio" in metrics_data
        assert "unresolved_issues" in metrics_data

        # 4. POST score calculation (/score)
        score_res = await client.post(f"/api/simulations/{sim_id}/score")
        assert score_res.status_code == 200
        score_data = score_res.json()
        assert score_data["simulation_id"] == sim_id
        assert "overall_score" in score_data
        assert "score_grade" in score_data
        assert "metric_breakdown" in score_data
        assert len(score_data["metric_breakdown"]) == 4

        # 5. GET cached score (/score)
        get_score_res = await client.get(f"/api/simulations/{sim_id}/score")
        assert get_score_res.status_code == 200
        assert get_score_res.json()["scoring_id"] == score_data["scoring_id"]

        # 6. GET score breakdown (/score/breakdown)
        breakdown_res = await client.get(f"/api/simulations/{sim_id}/score/breakdown")
        assert breakdown_res.status_code == 200
        breakdown_data = breakdown_res.json()
        assert len(breakdown_data) == 4
        metric_ids = [m["metric_id"] for m in breakdown_data]
        assert "risk_reduction" in metric_ids
        assert "response_time" in metric_ids
        assert "coordination" in metric_ids
        assert "unresolved_issues" in metric_ids

        # 7. Non-existent simulation 404
        bad_res = await client.post("/api/simulations/sim_non_existent/score")
        assert bad_res.status_code == 404


# ── 7. Additional Edge Case & Boundary Tests ──────────────────────────────────

def test_edge_case_zero_events_and_immediate_completion():
    """Simulation completing at tick 0 with 0 events and no actions."""
    snap = ScoringInputSnapshot(
        simulation_id="sim_zero_events",
        scenario_id="scenario_01",
        mode="no_coordination",
        start_tick=0,
        initial_tick=0,
        final_tick=0,
        simulation_status="COMPLETED",
        crisis_phase="DETECTION",
        unique_actions_taken=[],
        action_risk_reductions={},
        detection_tick=0,
        coordinated_action_tick=None,
        coordinated_action_occurred=False,
        total_countries=15,
        participating_countries=[],
        approving_countries=[],
        opposing_countries=[],
        undecided_countries=[],
        negotiation_sessions_count=0,
        negotiation_rounds_count=0,
        final_agreement_reached=False,
        events_count=0,
    )
    res = default_scoring_engine.evaluate_snapshot(snap)
    assert res.overall_score >= 0.0
    assert res.metrics.risk_final == 100.0
    assert res.metrics.risk_reduction_pct == 0.0
    assert res.metrics.coordination_ratio == 0.0
    assert res.score_grade in ("D", "F")


def test_edge_case_no_quorum_all_opposing_or_abstaining():
    """All countries either oppose or abstain; 0 approvals."""
    snap = ScoringInputSnapshot(
        simulation_id="sim_no_quorum",
        scenario_id="scenario_01",
        mode="coordinated",
        start_tick=0,
        final_tick=25,
        simulation_status="COMPLETED",
        crisis_phase="ESCALATION",
        unique_actions_taken=["early_detection"],
        total_countries=15,
        participating_countries=[f"country_{i:02d}" for i in range(1, 16)],
        approving_countries=[],
        opposing_countries=[f"country_{i:02d}" for i in range(1, 10)],
        undecided_countries=[f"country_{i:02d}" for i in range(10, 16)],
        negotiation_sessions_count=1,
        negotiation_rounds_count=3,
        final_agreement_reached=False,
        unresolved_issues_raw=["Liability", "Sovereignty", "Monitoring"],
    )
    res = default_scoring_engine.evaluate_snapshot(snap)
    assert res.metrics.coordination_ratio == 0.0
    assert res.metrics.countries_coordinating == 0
    assert res.metrics.agreement_reached is False
    assert res.metrics.unresolved_issues_count == 3


def test_edge_case_all_countries_supporting():
    """100% unanimous approval across all 15 countries with fast coordination."""
    all_c = [f"country_{i:02d}" for i in range(1, 16)]
    snap = ScoringInputSnapshot(
        simulation_id="sim_unanimous",
        scenario_id="scenario_01",
        mode="coordinated",
        start_tick=0,
        final_tick=12,
        simulation_status="COMPLETED",
        crisis_phase="CONTAINED",
        unique_actions_taken=[
            "early_detection",
            "international_alert",
            "system_containment",
            "joint_investigation",
            "evidence_sharing",
        ],
        detection_tick=0,
        coordinated_action_tick=8,
        coordinated_action_occurred=True,
        total_countries=15,
        participating_countries=all_c,
        approving_countries=all_c,
        opposing_countries=[],
        undecided_countries=[],
        negotiation_sessions_count=1,
        negotiation_rounds_count=1,
        final_agreement_reached=True,
        unresolved_issues_raw=[],
    )
    res = default_scoring_engine.evaluate_snapshot(snap)
    assert res.metrics.coordination_ratio == 1.0
    assert res.metrics.countries_coordinating == 15
    assert res.metrics.risk_reduction_pct >= 80.0
    assert res.score_grade == "A"
    assert res.overall_score >= 85.0


def test_edge_case_max_negotiation_rounds_unresolved():
    """Negotiation hits max rounds (3) without resolving and collapses."""
    snap = ScoringInputSnapshot(
        simulation_id="sim_max_rounds_failed",
        scenario_id="scenario_01",
        mode="coordinated",
        start_tick=0,
        final_tick=45,
        simulation_status="COMPLETED",
        crisis_phase="CRITICAL",
        unique_actions_taken=["early_detection"],
        detection_tick=0,
        coordinated_action_tick=None,
        coordinated_action_occurred=False,
        total_countries=15,
        participating_countries=[f"country_{i:02d}" for i in range(1, 16)],
        approving_countries=["country_01", "country_02"],
        opposing_countries=[f"country_{i:02d}" for i in range(3, 16)],
        undecided_countries=[],
        negotiation_sessions_count=1,
        negotiation_rounds_count=3,
        final_agreement_reached=False,
        final_negotiation_status="COLLAPSED",
        unresolved_issues_raw=["Liability", "Attribution", "Sanctions", "Audit Access", "Export Controls"],
    )
    res = default_scoring_engine.evaluate_snapshot(snap)
    assert res.metrics.agreement_reached is False
    assert res.metrics.negotiation_rounds == 3
    assert res.metrics.unresolved_issues_count == 5
    assert res.metrics.coordination_ratio == pytest.approx(2 / 15, 0.001)
    assert res.score_grade in ("D", "F")


def test_invalid_scoring_input_validation():
    """Scoring engine properly rejects invalid snapshots with empty simulation_id or negative countries."""
    with pytest.raises(ValueError, match="simulation_id cannot be empty"):
        snap_bad_id = ScoringInputSnapshot(
            simulation_id="",
            scenario_id="scenario_01",
            mode="coordinated",
            final_tick=10,
            simulation_status="COMPLETED",
            crisis_phase="DETECTION",
            total_countries=15,
        )
        default_scoring_engine.evaluate_snapshot(snap_bad_id)


def test_scoring_orm_models():
    """Validates instantiation of SQLAlchemy ORM models."""
    from app.models.scoring_orm import MetricResultORM, ScoringResultORM, ScoringSnapshotORM

    orm_score = ScoringResultORM(
        scoring_id="score_orm_test",
        simulation_id="sim_orm_test",
        scenario_id="scenario_01",
        simulation_mode="coordinated",
        formula_version="1.0",
        overall_score=88.5,
        score_grade="A",
        performance_headline="Optimal Multilateralism",
        simulation_status="COMPLETED",
        calculated_at_tick=15,
        is_authoritative=True,
        mode_comparison_ready=True,
    )
    assert orm_score.scoring_id == "score_orm_test"
    assert orm_score.overall_score == 88.5

    orm_metric = MetricResultORM(
        scoring_id="score_orm_test",
        metric_id="risk_reduction",
        name="Risk Reduction",
        raw_value=75.0,
        unit="%",
        display_value="↓75%",
        normalized_score=75.0,
        weight=0.25,
        weighted_score=18.75,
        interpretation="Strong risk mitigation",
        evidence={"initial_risk": 100.0},
    )
    assert orm_metric.metric_id == "risk_reduction"

    orm_snap = ScoringSnapshotORM(
        snapshot_id="snap_orm_test",
        simulation_id="sim_orm_test",
        scenario_id="scenario_01",
        mode="coordinated",
        final_tick=15,
        snapshot_data={"test": True},
    )
    assert orm_snap.snapshot_id == "snap_orm_test"


@pytest.mark.anyio
async def test_api_require_completed_validation():
    """Verifies that require_completed=True rejects a RUNNING simulation with 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        create_res = await client.post(
            "/api/simulations",
            json={"scenario_id": "scenario_01", "mode": "coordinated"},
        )
        sim_id = create_res.json()["simulation_id"]
        # Step once (now RUNNING)
        await client.post(f"/api/simulations/{sim_id}/step")

        # Request score with require_completed=True should fail 400
        res = await client.post(f"/api/simulations/{sim_id}/score?require_completed=true")
        assert res.status_code == 400
        assert "requires a COMPLETED simulation" in res.json()["detail"]

        # Regular request with require_completed=False (default) should succeed
        res_ok = await client.post(f"/api/simulations/{sim_id}/score")
        assert res_ok.status_code == 200


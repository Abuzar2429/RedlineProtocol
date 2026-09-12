"""
Deterministic Scoring Engine for AI Governance Crisis Simulator (Phase 7).

Orchestrates evaluation of simulation outcomes:
- Consumes authoritative SimulationState or ScoringInputSnapshot
- Evaluates the exact four specification metrics
- Computes weighted composite score and grade
- Emits structured, explainable, reproducible ScoringResult
- Provides live SimulationMetrics calculation for the dashboard metrics bar
- Zero LLM authority
"""
import logging
import uuid
from typing import List, Optional

from app.schemas.scoring_models import (
    MetricResult,
    ScoringInputSnapshot,
    ScoringResult,
    SimulationMetrics,
)
from app.schemas.simulation_models import SimulationState
from app.scoring.metrics import (
    SCORING_FORMULA_VERSION,
    compute_coordination_score,
    compute_overall_score,
    compute_response_time,
    compute_risk_score,
    extract_and_score_unresolved_issues,
)
from app.scoring.snapshot import ScoringSnapshotBuilder

logger = logging.getLogger(__name__)


class DeterministicScoringEngine:
    """
    Pure deterministic scoring engine. Evaluates simulation snapshots.
    """

    def __init__(self, formula_version: str = SCORING_FORMULA_VERSION):
        self.formula_version = formula_version

    def evaluate_snapshot(self, snapshot: ScoringInputSnapshot) -> ScoringResult:
        """
        Pure evaluation of a ScoringInputSnapshot.
        Guaranteed to produce identical results for identical snapshots.
        """
        logger.info(
            "Scoring started for simulation [%s] (mode=%s, tick=%d)",
            snapshot.simulation_id,
            snapshot.mode,
            snapshot.final_tick,
        )

        if not snapshot.simulation_id:
            logger.error("Scoring validation failure: simulation_id is empty")
            raise ValueError("ScoringInputSnapshot simulation_id cannot be empty")
        if snapshot.total_countries < 0:
            logger.error("Scoring validation failure: total_countries is negative (%d)", snapshot.total_countries)
            raise ValueError("ScoringInputSnapshot total_countries cannot be negative")

        # 1. Metric 3 first: Coordination Ratio (needed as multiplier for Metric 1)
        approving_count = len(snapshot.approving_countries)
        coord_ratio, metric_coordination = compute_coordination_score(
            approving_count=approving_count,
            total_countries=snapshot.total_countries,
        )
        logger.debug("Metric calculated: Coordination = %s (%.2f)", metric_coordination.display_value, coord_ratio)

        # 2. Metric 1: Risk Reduction & Final Risk
        risk_final, risk_reduction_pct, metric_risk = compute_risk_score(
            unique_actions=snapshot.unique_actions_taken,
            coordination_ratio=coord_ratio,
            custom_reductions=snapshot.action_risk_reductions,
        )
        logger.debug("Metric calculated: Risk Reduction = %s (final=%.1f)", metric_risk.display_value, risk_final)

        # 3. Metric 2: Response Time
        response_time_min, metric_response = compute_response_time(
            detection_tick=snapshot.detection_tick,
            coordinated_action_tick=snapshot.coordinated_action_tick,
            final_tick=snapshot.final_tick,
        )
        logger.debug("Metric calculated: Response Time = %s", metric_response.display_value)

        # 4. Metric 4: Unresolved Issues
        unresolved_issues, unresolved_count, metric_unresolved = extract_and_score_unresolved_issues(
            unresolved_issues_raw=snapshot.unresolved_issues_raw,
            negotiation_rounds_count=snapshot.negotiation_rounds_count,
        )
        logger.debug("Metric calculated: Unresolved Issues = %s", metric_unresolved.display_value)

        # 5. Assemble Metric Results
        metric_breakdown: List[MetricResult] = [
            metric_risk,
            metric_response,
            metric_coordination,
            metric_unresolved,
        ]

        # 6. Overall Composite Score & Grade
        overall_score, grade, headline = compute_overall_score(metric_breakdown)

        # 7. Assemble Spec §6.5 SimulationMetrics Object
        spec_metrics = SimulationMetrics(
            risk_initial=100.0,
            risk_final=risk_final,
            risk_reduction_pct=risk_reduction_pct,
            response_time_minutes=response_time_min,
            coordination_ratio=coord_ratio,
            countries_coordinating=approving_count,
            countries_total=snapshot.total_countries,
            unresolved_issues=unresolved_issues,
            unresolved_issues_count=unresolved_count,
            negotiation_rounds=snapshot.negotiation_rounds_count,
            agreement_reached=snapshot.final_agreement_reached,
            simulation_mode=snapshot.mode,
        )

        scoring_id = f"score_{uuid.uuid4().hex[:12]}"

        logger.info(
            "Scoring completed for simulation [%s] mode=%s overall=%.2f grade=%s risk_final=%.1f resp_time=%dm coord=%.2f",
            snapshot.simulation_id,
            snapshot.mode,
            overall_score,
            grade,
            risk_final,
            response_time_min,
            coord_ratio,
        )

        return ScoringResult(
            scoring_id=scoring_id,
            simulation_id=snapshot.simulation_id,
            scenario_id=snapshot.scenario_id,
            simulation_mode=snapshot.mode,
            formula_version=self.formula_version,
            overall_score=overall_score,
            score_grade=grade,
            performance_headline=headline,
            simulation_status=snapshot.simulation_status,
            calculated_at_tick=snapshot.final_tick,
            metrics=spec_metrics,
            metric_breakdown=metric_breakdown,
            input_snapshot=snapshot,
            mode_comparison_ready=True,
            is_authoritative=True,
        )

    def evaluate_state(self, state: SimulationState) -> ScoringResult:
        """
        Builds a snapshot from state and computes full ScoringResult.
        """
        snapshot = ScoringSnapshotBuilder.from_simulation_state(state)
        return self.evaluate_snapshot(snapshot)

    def evaluate_live_metrics(self, state: SimulationState) -> SimulationMetrics:
        """
        Fast computation of live SimulationMetrics for the dashboard live metrics bar.
        """
        snapshot = ScoringSnapshotBuilder.from_simulation_state(state)
        scoring_res = self.evaluate_snapshot(snapshot)
        return scoring_res.metrics


# Default singleton scoring engine instance
default_scoring_engine = DeterministicScoringEngine()

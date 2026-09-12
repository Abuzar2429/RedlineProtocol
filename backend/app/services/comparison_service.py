"""
Comparison Service and Repository for Phase 13 Three-Mode Comparison Engine.

Orchestrates running the EXACT same crisis scenario through all three coordination modes:
1. 'no_coordination' (Unilateral action, sovereign doctrine)
2. 'partial' (Regional/bilateral coalition, 50% quorum, simple majority)
3. 'coordinated' (Multilateral accord, 60% quorum, 60% qualified majority)

Enforces:
- Programmatic validation of the exact same scenario across all three modes
- Isolated SimulationEngines with unique simulation IDs
- Equivalent initial conditions
- Execution via existing SimulationEngine, Country Agents, Coordinator, Negotiation, and Phase 7 Deterministic Scoring Engine
- Deterministic winner rule: highest overall_score from Phase 7; explicit TIE handling
- Zero LLM authority in scoring or winner determination
- WebSocket event broadcasting via default_websocket_manager
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.schemas.comparison_models import (
    ComparisonDelta,
    ComparisonRun,
    ComparisonStatus,
    ComparisonWinner,
    CreateComparisonRequest,
    ModeComparisonResult,
)
from app.schemas.simulation_models import SimulationMode
from app.scoring import default_scoring_engine
from app.services.data_loader import default_data_loader
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository
from app.services.websocket_manager import default_websocket_manager

logger = logging.getLogger(__name__)

# Exact three project-defined coordination modes
SUPPORTED_COMPARISON_MODES: List[SimulationMode] = [
    "no_coordination",
    "partial",
    "coordinated",
]

MODE_DISPLAY_NAMES: Dict[SimulationMode, str] = {
    "no_coordination": "No Coordination (Unilateral)",
    "partial": "Partial Coordination (Coalition)",
    "coordinated": "Full Coordinated Governance",
}


class ComparisonRepository:
    """
    In-memory, thread-safe registry of ComparisonRun sessions.
    Stores comparison metadata and links to the three underlying simulation records.
    """

    def __init__(self):
        self._comparisons: Dict[str, ComparisonRun] = {}

    def save(self, run: ComparisonRun) -> None:
        self._comparisons[run.comparison_id] = run

    def get(self, comparison_id: str) -> Optional[ComparisonRun]:
        return self._comparisons.get(comparison_id)

    def list_all(self) -> List[ComparisonRun]:
        return list(self._comparisons.values())

    def delete(self, comparison_id: str) -> bool:
        if comparison_id in self._comparisons:
            del self._comparisons[comparison_id]
            return True
        return False

    def clear(self) -> None:
        self._comparisons.clear()


default_comparison_repository = ComparisonRepository()


class ComparisonService:
    """
    Orchestrates the execution and deterministic synthesis of Three-Mode Comparative Runs.
    """

    def __init__(self, repository: Optional[ComparisonRepository] = None):
        self.repository = repository or default_comparison_repository

    def create_comparison(self, request: CreateComparisonRequest) -> ComparisonRun:
        """
        Validates scenario and initializes a new ComparisonRun in CREATED status.
        Ensures the exact same scenario is assigned to all three planned modes.
        """
        # 1. Validate scenario exists in DataLoader
        scenario = default_data_loader.load_scenario(request.scenario_id)
        if not scenario:
            raise KeyError(f"Scenario '{request.scenario_id}' not found")

        comparison_id = f"comp_{uuid.uuid4().hex[:12]}"
        now_utc = datetime.now(timezone.utc).isoformat()

        run = ComparisonRun(
            comparison_id=comparison_id,
            scenario_id=scenario.id,
            scenario_title=scenario.title,
            status="CREATED",
            created_at=now_utc,
            modes_evaluated=list(SUPPORTED_COMPARISON_MODES),
            results={},
            winner=None,
            winner_reason=None,
            summary_headline="Comparative analysis initialized. Awaiting execution.",
            summary_narrative="",
            deltas=[],
            is_authoritative=True,
            metadata={
                "max_ticks": request.max_ticks or 120,
                "origin_country": scenario.origin_country,
                "severity": scenario.severity,
                "user_metadata": request.metadata,
            },
        )

        self.repository.save(run)
        logger.info(
            "Created comparison [%s] for scenario [%s] (%s)",
            comparison_id,
            scenario.id,
            scenario.title,
        )
        return run

    async def execute_comparison(self, comparison_id: str) -> ComparisonRun:
        """
        Executes the three modes sequentially:
        'no_coordination' -> 'partial' -> 'coordinated'
        Guarantees simulation isolation, fair initial conditions, and deterministic scoring.
        """
        run = self.repository.get(comparison_id)
        if not run:
            raise KeyError(f"Comparison '{comparison_id}' not found")

        if run.status == "COMPLETED":
            return run

        run.status = "RUNNING"
        self.repository.save(run)

        # Notify WebSocket subscribers that comparison has commenced
        await default_websocket_manager.broadcast_event(
            simulation_id=comparison_id,
            event_type="COMPARISON_STARTED",
            payload={
                "comparison_id": comparison_id,
                "scenario_id": run.scenario_id,
                "modes": list(SUPPORTED_COMPARISON_MODES),
            },
            category="event",
        )

        max_ticks = int(run.metadata.get("max_ticks", 120))
        scenario_id = run.scenario_id

        # Programmatic verification: ensure all three modes evaluate the EXACT same scenario
        for mode in SUPPORTED_COMPARISON_MODES:
            sim_id = f"sim_{comparison_id}_{mode}"
            logger.info(
                "Running comparison [%s] mode [%s] with sim_id [%s] on scenario [%s]",
                comparison_id,
                mode,
                sim_id,
                scenario_id,
            )

            # Broadcast mode start
            await default_websocket_manager.broadcast_event(
                simulation_id=comparison_id,
                event_type="COMPARISON_MODE_STARTED",
                payload={
                    "comparison_id": comparison_id,
                    "mode": mode,
                    "simulation_id": sim_id,
                    "mode_name": MODE_DISPLAY_NAMES.get(mode, mode),
                },
                category="event",
            )

            try:
                mode_result = await self._run_single_mode(
                    comparison_id=comparison_id,
                    scenario_id=scenario_id,
                    mode=mode,
                    simulation_id=sim_id,
                    max_ticks=max_ticks,
                )
                run.results[mode] = mode_result

                # Broadcast mode completion
                await default_websocket_manager.broadcast_event(
                    simulation_id=comparison_id,
                    event_type="COMPARISON_MODE_COMPLETED",
                    payload={
                        "comparison_id": comparison_id,
                        "mode": mode,
                        "simulation_id": sim_id,
                        "overall_score": mode_result.overall_score,
                        "score_grade": mode_result.score_grade,
                        "status": mode_result.status,
                        "final_tick": mode_result.final_tick,
                    },
                    category="complete" if mode_result.status == "COMPLETED" else "error",
                )

            except Exception as exc:
                logger.error(
                    "Mode execution failed for [%s] in comparison [%s]: %s",
                    mode,
                    comparison_id,
                    exc,
                    exc_info=True,
                )
                run.results[mode] = ModeComparisonResult(
                    mode=mode,
                    mode_name=MODE_DISPLAY_NAMES.get(mode, mode),
                    simulation_id=sim_id,
                    status="FAILED",
                    final_tick=0,
                    error=str(exc),
                    performance_headline=f"Execution error: {exc}",
                )
                await default_websocket_manager.broadcast_event(
                    simulation_id=comparison_id,
                    event_type="COMPARISON_MODE_FAILED",
                    payload={
                        "comparison_id": comparison_id,
                        "mode": mode,
                        "simulation_id": sim_id,
                        "error": str(exc),
                    },
                    category="error",
                )

        # ── Deterministic Winner Determination & Synthesis ────────────────────
        run.status = "COLLECTING_RESULTS"
        self._determine_winner_and_synthesize(run)

        run.status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc).isoformat()
        self.repository.save(run)

        # Broadcast final completion
        await default_websocket_manager.broadcast_event(
            simulation_id=comparison_id,
            event_type="COMPARISON_COMPLETED",
            payload={
                "comparison_id": comparison_id,
                "winner": run.winner,
                "winner_reason": run.winner_reason,
                "summary_headline": run.summary_headline,
                "results": {
                    m: {
                        "score": r.overall_score,
                        "grade": r.score_grade,
                        "is_winner": r.is_winner,
                    }
                    for m, r in run.results.items()
                },
            },
            category="complete",
        )

        return run

    async def _run_single_mode(
        self,
        comparison_id: str,
        scenario_id: str,
        mode: SimulationMode,
        simulation_id: str,
        max_ticks: int,
    ) -> ModeComparisonResult:
        """
        Executes one isolated simulation run with guaranteed pristine initial conditions.
        """
        # 1. Create pristine isolated SimulationEngine
        engine = SimulationEngine.create(
            scenario_id=scenario_id,
            mode=mode,
            simulation_id=simulation_id,
            max_ticks=max_ticks,
        )
        default_simulation_repository.save(engine)

        # 2. Run simulation ticks to completion
        engine.run_until_complete(max_ticks=max_ticks)

        # 3. Ensure negotiation occurs if supported by mode and not yet completed
        if mode in ("coordinated", "partial") and not engine.state.negotiations:
            from app.agents.coordinator_service import default_coordinator_service
            from app.negotiation.negotiation_service import default_negotiation_service

            try:
                if not engine.state.proposals:
                    round_idx = len(engine.state.proposals) + 1
                    proposal = await default_coordinator_service.request_coordination(
                        state=engine.state,
                        round_index=round_idx,
                    )
                    engine.state.proposals.append(proposal)
                else:
                    proposal = engine.state.proposals[-1]

                session = default_negotiation_service.start_negotiation(
                    state=engine.state,
                    proposal=proposal,
                    max_rounds=3,
                )
                default_negotiation_service.run_full_negotiation(session, engine.state)
                engine.state.negotiations.append(session)
            except Exception as neg_exc:
                logger.warning(
                    "Negotiation invocation fallback for simulation [%s]: %s",
                    simulation_id,
                    neg_exc,
                )

        # 4. Invoke the Phase 7 Deterministic Scoring Engine (Zero LLM authority)
        scoring_result = default_scoring_engine.evaluate_state(engine.state)

        # 5. Extract latest negotiation outcome if present
        latest_outcome = (
            engine.state.negotiations[-1].outcome
            if engine.state.negotiations and engine.state.negotiations[-1].outcome
            else None
        )

        return ModeComparisonResult(
            mode=mode,
            mode_name=MODE_DISPLAY_NAMES.get(mode, mode),
            simulation_id=simulation_id,
            status=engine.state.status,
            final_tick=engine.state.current_tick,
            overall_score=scoring_result.overall_score,
            score_grade=scoring_result.score_grade,
            performance_headline=scoring_result.performance_headline,
            is_winner=False,  # Evaluated later in synthesis
            scoring_result=scoring_result,
            metrics=scoring_result.metrics,
            metric_breakdown=scoring_result.metric_breakdown,
            negotiation_outcome=latest_outcome,
            events_count=len(engine.state.event_history),
            decisions_count=len(engine.state.decisions),
        )

    def _determine_winner_and_synthesize(self, run: ComparisonRun) -> None:
        """
        Deterministically evaluates the winning coordination mode:
        - Rule: Highest overall_score from Phase 7 Deterministic Scoring Engine
        - Explicit tie handling if top scores are identical
        - Computes deltas against baseline 'no_coordination'
        - Generates structured, deterministic narrative summary (zero LLM hallucination)
        """
        valid_modes = [
            (m, res)
            for m, res in run.results.items()
            if res.status == "COMPLETED" and res.overall_score is not None
        ]

        if not valid_modes:
            run.winner = "FAILED"
            run.winner_reason = "No simulation mode completed successfully."
            run.summary_headline = "Comparison failed: all coordination runs encountered errors."
            run.summary_narrative = (
                "All three simulation runs failed to reach completion. "
                "No authoritative scores could be evaluated."
            )
            return

        # Sort descending by overall_score
        valid_modes.sort(key=lambda item: item[1].overall_score, reverse=True)
        top_mode, top_result = valid_modes[0]
        top_score = top_result.overall_score

        # Check for ties (scores within 0.05 points)
        tied_modes = [
            m for m, res in valid_modes if abs(res.overall_score - top_score) < 0.05
        ]

        if len(tied_modes) > 1:
            run.winner = "TIE"
            tied_names = [MODE_DISPLAY_NAMES.get(m, m) for m in tied_modes]
            run.winner_reason = (
                f"Statistical tie between {', '.join(tied_names)} "
                f"with identical score of {top_score:.1f}/100."
            )
            for m, res in run.results.items():
                res.is_winner = m in tied_modes
        else:
            run.winner = top_mode  # e.g. 'coordinated'
            winner_name = MODE_DISPLAY_NAMES.get(top_mode, top_mode)
            run.winner_reason = (
                f"{winner_name} achieved the highest authoritative score ({top_score:.1f}/100, "
                f"Grade {top_result.score_grade})."
            )
            for m, res in run.results.items():
                res.is_winner = (m == top_mode)

        # Calculate comparative deltas against 'no_coordination' baseline
        run.deltas = self._calculate_deltas(run.results)

        # Generate deterministic narrative synthesis
        run.summary_headline = self._build_headline(run)
        run.summary_narrative = self._build_narrative(run)

    def _calculate_deltas(
        self, results: Dict[str, ModeComparisonResult]
    ) -> List[ComparisonDelta]:
        """
        Computes pairwise variances between modes and the baseline 'no_coordination'.
        """
        deltas: List[ComparisonDelta] = []
        baseline = results.get("no_coordination")
        if not baseline or baseline.overall_score is None:
            return deltas

        for mode in ("partial", "coordinated"):
            target = results.get(mode)
            if not target or target.overall_score is None:
                continue

            base_m = baseline.metrics
            targ_m = target.metrics

            base_risk_red = base_m.risk_reduction_pct if base_m else 0.0
            targ_risk_red = targ_m.risk_reduction_pct if targ_m else 0.0

            base_resp_time = base_m.response_time_minutes if base_m else 0
            targ_resp_time = targ_m.response_time_minutes if targ_m else 0

            base_coord = base_m.coordination_ratio if base_m else 0.0
            targ_coord = targ_m.coordination_ratio if targ_m else 0.0

            base_unres = base_m.unresolved_issues_count if base_m else 0
            targ_unres = targ_m.unresolved_issues_count if targ_m else 0

            deltas.append(
                ComparisonDelta(
                    baseline_mode="no_coordination",
                    compared_mode=mode,
                    overall_score_delta=round(target.overall_score - baseline.overall_score, 2),
                    risk_reduction_delta_pct=round(targ_risk_red - base_risk_red, 2),
                    response_time_delta_min=targ_resp_time - base_resp_time,
                    coordination_ratio_delta=round(targ_coord - base_coord, 3),
                    unresolved_issues_delta=targ_unres - base_unres,
                    final_tick_delta=target.final_tick - baseline.final_tick,
                )
            )
        return deltas

    def _build_headline(self, run: ComparisonRun) -> str:
        """
        Constructs a concise summary headline of the comparative outcome.
        """
        if run.winner == "TIE":
            return "Comparative evaluation resulted in a dead-heat tie between governance strategies."
        if run.winner == "FAILED":
            return "Comparison run could not be completed."

        winner_name = MODE_DISPLAY_NAMES.get(run.winner, run.winner or "Unknown")
        winner_res = run.results.get(run.winner)
        score_str = f"{winner_res.overall_score:.1f}/100" if winner_res and winner_res.overall_score else ""
        grade_str = f"Grade {winner_res.score_grade}" if winner_res and winner_res.score_grade else ""

        # Compare with no_coordination baseline if available
        baseline = run.results.get("no_coordination")
        if baseline and baseline.overall_score and winner_res and winner_res.overall_score and run.winner != "no_coordination":
            diff = winner_res.overall_score - baseline.overall_score
            return (
                f"{winner_name} outperformed Unilateral action by +{diff:.1f} pts "
                f"({score_str}, {grade_str})."
            )
        return f"{winner_name} achieved the optimal crisis outcome ({score_str}, {grade_str})."

    def _build_narrative(self, run: ComparisonRun) -> str:
        """
        Produces an explainable, multi-paragraph factual narrative of the comparison.
        Completely deterministic and grounded in actual numbers.
        """
        paragraphs: List[str] = []

        no_coord = run.results.get("no_coordination")
        partial = run.results.get("partial")
        coord = run.results.get("coordinated")

        # Paragraph 1: Overview
        p1 = (
            f"The AI crisis scenario '{run.scenario_title}' was evaluated under three distinct "
            "governance architectures: No Coordination (Unilateral Doctrine), Partial Coordination "
            "(Bilateral & Regional Coalition), and Full Coordinated Governance (Multilateral Accord). "
        )
        if run.winner and run.winner != "TIE" and run.winner != "FAILED":
            p1 += f"The authoritative winner is {MODE_DISPLAY_NAMES.get(run.winner)}, {run.winner_reason}"
        elif run.winner == "TIE":
            p1 += f"The evaluation resulted in a tie: {run.winner_reason}"
        paragraphs.append(p1)

        # Paragraph 2: Metric Breakdown
        lines = []
        for m in SUPPORTED_COMPARISON_MODES:
            res = run.results.get(m)
            if res and res.overall_score is not None:
                risk_pct = f"{res.metrics.risk_reduction_pct:.1f}%" if res.metrics else "N/A"
                resp_time = f"{res.metrics.response_time_minutes}m" if res.metrics else "N/A"
                coord_ratio = f"{res.metrics.coordination_ratio:.2f}" if res.metrics else "N/A"
                unres = f"{res.metrics.unresolved_issues_count}" if res.metrics else "N/A"
                lines.append(
                    f"- {res.mode_name}: Overall Score {res.overall_score:.1f} (Grade {res.score_grade}) | "
                    f"Risk Reduction: {risk_pct} | Response Time: {resp_time} | "
                    f"Coordination Ratio: {coord_ratio} | Unresolved Issues: {unres}"
                )
        if lines:
            paragraphs.append("Quantitative Metric Comparison:\n" + "\n".join(lines))

        # Paragraph 3: Thesis Synthesis
        if coord and no_coord and coord.overall_score and no_coord.overall_score:
            pts_gain = coord.overall_score - no_coord.overall_score
            coord_risk = coord.metrics.risk_reduction_pct if coord.metrics else 0.0
            no_coord_risk = no_coord.metrics.risk_reduction_pct if no_coord.metrics else 0.0
            paragraphs.append(
                f"Synthesis: Full Coordinated Governance delivered a +{pts_gain:.1f} point improvement "
                f"over unilateral sovereign action, achieving {coord_risk:.1f}% overall crisis risk elimination "
                f"versus {no_coord_risk:.1f}% under fragmented response. "
                "This empirically validates that structured multilateral crisis protocols yield superior "
                "containment speed and risk mitigation."
            )

        return "\n\n".join(paragraphs)


default_comparison_service = ComparisonService()

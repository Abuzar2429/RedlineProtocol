"""
Scoring REST API routes (Phase 7).

Provides deterministic evaluation of simulation outcomes:
- POST /api/simulations/{id}/score: Triggers deterministic evaluation
- GET  /api/simulations/{id}/score: Retrieves computed evaluation
- GET  /api/simulations/{id}/metrics: Retrieves live spec metrics
- GET  /api/simulations/{id}/score/breakdown: Retrieves detailed metric breakdown with evidence
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.scoring_models import MetricResult, ScoringResult, SimulationMetrics
from app.scoring import default_scoring_engine, default_scoring_repository
from app.services.simulation.repository import default_simulation_repository
from app.services.websocket_manager import default_websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simulations", tags=["scoring"])


def _validate_scoreable_state(state, require_completed: bool = False) -> None:
    """
    Validates that a simulation is in a valid, scoreable state according to rules.
    """
    if state.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Simulation '{state.simulation_id}' is in FAILED state and cannot be scored",
        )
    if require_completed is True and state.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Simulation '{state.simulation_id}' is still in status '{state.status}'. "
                "Final score calculation requires a COMPLETED simulation."
            ),
        )
    valid_modes = {"no_coordination", "partial", "coordinated"}
    if state.mode not in valid_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported coordination mode '{state.mode}'. Expected one of {valid_modes}",
        )
    if not state.countries or len(state.countries) < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Corrupted simulation state: no registered countries found",
        )


@router.post("/{simulation_id}/score", response_model=ScoringResult, status_code=status.HTTP_200_OK)
async def score_simulation(
    simulation_id: str,
    require_completed: bool = Query(
        False,
        description="If True, rejects simulations that have not reached COMPLETED status",
    ),
) -> ScoringResult:
    """
    Evaluates the simulation using the deterministic scoring engine.
    Stores and returns the complete ScoringResult.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    _validate_scoreable_state(engine.state, require_completed=bool(require_completed is True))

    try:
        score_result = default_scoring_engine.evaluate_state(engine.state)
        default_scoring_repository.save(score_result)
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="SCORING_COMPLETED",
            payload={
                "scoring_id": score_result.scoring_id,
                "overall_score": score_result.overall_score,
                "score_grade": score_result.score_grade,
                "performance_headline": score_result.performance_headline,
            },
            tick=score_result.calculated_at_tick,
            timestamp=f"T+{score_result.calculated_at_tick:02d}",
            category="metrics",
        )
        return score_result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Scoring failed for simulation %s: %s", simulation_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deterministic scoring calculation failed: {str(exc)}",
        )


@router.get("/{simulation_id}/score", response_model=ScoringResult)
async def get_simulation_score(
    simulation_id: str,
    recalculate: bool = Query(False, description="Force re-scoring instead of returning cached result"),
    require_completed: bool = Query(False, description="Require simulation to be completed"),
) -> ScoringResult:
    """
    Retrieves the score for a simulation.
    If not yet evaluated (or if recalculate=True), calculates and caches it automatically.
    """
    if recalculate is not True:
        cached = default_scoring_repository.get(simulation_id)
        if cached:
            return cached

    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    _validate_scoreable_state(engine.state, require_completed=bool(require_completed is True))

    score_result = default_scoring_engine.evaluate_state(engine.state)
    default_scoring_repository.save(score_result)
    return score_result


@router.get("/{simulation_id}/metrics", response_model=SimulationMetrics)
async def get_simulation_metrics(simulation_id: str) -> SimulationMetrics:
    """
    Retrieves live SimulationMetrics matching Spec §6.5 & §7.1.
    Evaluates current state for the live dashboard metrics bar.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    return default_scoring_engine.evaluate_live_metrics(engine.state)


@router.get("/{simulation_id}/score/breakdown", response_model=List[MetricResult])
async def get_score_breakdown(simulation_id: str) -> List[MetricResult]:
    """
    Retrieves the detailed four-metric breakdown with structured evidence.
    """
    cached = default_scoring_repository.get(simulation_id)
    if cached:
        return cached.metric_breakdown

    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    _validate_scoreable_state(engine.state, require_completed=False)
    score_result = default_scoring_engine.evaluate_state(engine.state)
    default_scoring_repository.save(score_result)
    return score_result.metric_breakdown

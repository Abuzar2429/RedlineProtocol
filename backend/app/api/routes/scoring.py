"""
Scoring REST API routes (Phase 7).

Provides deterministic evaluation of simulation outcomes:
- POST /api/simulations/{id}/score: Triggers deterministic evaluation
- GET  /api/simulations/{id}/score: Retrieves computed evaluation
- GET  /api/simulations/{id}/metrics: Retrieves live spec metrics
- GET  /api/simulations/{id}/score/breakdown: Retrieves detailed metric breakdown with evidence
"""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.schemas.scoring_models import MetricResult, ScoringResult, SimulationMetrics
from app.scoring import default_scoring_engine, default_scoring_repository
from app.services.simulation.repository import default_simulation_repository

router = APIRouter(prefix="/api/simulations", tags=["scoring"])


@router.post("/{simulation_id}/score", response_model=ScoringResult, status_code=status.HTTP_200_OK)
async def score_simulation(simulation_id: str) -> ScoringResult:
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

    try:
        score_result = default_scoring_engine.evaluate_state(engine.state)
        default_scoring_repository.save(score_result)
        return score_result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deterministic scoring failed: {str(exc)}",
        )


@router.get("/{simulation_id}/score", response_model=ScoringResult)
async def get_simulation_score(simulation_id: str) -> ScoringResult:
    """
    Retrieves the score for a simulation.
    If not yet evaluated, calculates and caches it automatically.
    """
    cached = default_scoring_repository.get(simulation_id)
    if cached:
        return cached

    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

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
    score = await get_simulation_score(simulation_id)
    return score.metric_breakdown

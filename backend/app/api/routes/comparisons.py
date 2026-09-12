"""
REST API routes for Phase 13 Three-Mode Comparison Engine.

Provides endpoints to:
- POST /api/comparisons: Create and execute a 3-mode comparison run
- GET  /api/comparisons: List all comparative evaluation runs
- GET  /api/comparisons/{comparison_id}: Retrieve full comparison run results
- GET  /api/comparisons/{comparison_id}/status: Retrieve lightweight lifecycle status
- GET  /api/comparisons/{comparison_id}/modes/{mode}: Retrieve detailed result for a single mode
- POST /api/comparisons/{comparison_id}/run: Execute or re-execute a comparison session
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.schemas.comparison_models import (
    ComparisonRun,
    CreateComparisonRequest,
    ModeComparisonResult,
)
from app.services.comparison_service import (
    SUPPORTED_COMPARISON_MODES,
    default_comparison_repository,
    default_comparison_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/comparisons", tags=["comparisons"])


@router.post("", response_model=ComparisonRun, status_code=status.HTTP_201_CREATED)
async def create_and_run_comparison(
    request: CreateComparisonRequest,
    background: bool = Query(
        False,
        description="If True, runs comparison asynchronously in background and returns CREATED run immediately.",
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> ComparisonRun:
    """
    Creates a new Three-Mode Comparative Run for the specified crisis scenario.
    By default runs synchronously and returns the fully evaluated comparison.
    """
    try:
        run = default_comparison_service.create_comparison(request)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario not found: {exc}",
        )
    except Exception as exc:
        logger.error("Failed to initialize comparison: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initialize comparison: {exc}",
        )

    if background:
        if background_tasks:
            background_tasks.add_task(default_comparison_service.execute_comparison, run.comparison_id)
        return run

    # Execute synchronously
    try:
        completed_run = await default_comparison_service.execute_comparison(run.comparison_id)
        return completed_run
    except Exception as exc:
        logger.error("Execution failed for comparison [%s]: %s", run.comparison_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison execution failed: {exc}",
        )


@router.get("", response_model=List[ComparisonRun])
async def list_comparisons() -> List[ComparisonRun]:
    """
    Lists all comparison runs registered in the system.
    """
    return default_comparison_repository.list_all()


@router.get("/{comparison_id}", response_model=ComparisonRun)
async def get_comparison(comparison_id: str) -> ComparisonRun:
    """
    Retrieves full details, deltas, and mode results for a comparison run.
    """
    run = default_comparison_repository.get(comparison_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison '{comparison_id}' not found",
        )
    return run


@router.get("/{comparison_id}/status")
async def get_comparison_status(comparison_id: str) -> Dict[str, Any]:
    """
    Retrieves lightweight execution status for progress bars and pollers.
    """
    run = default_comparison_repository.get(comparison_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison '{comparison_id}' not found",
        )
    completed_modes = sum(1 for res in run.results.values() if res.status == "COMPLETED")
    return {
        "comparison_id": run.comparison_id,
        "scenario_id": run.scenario_id,
        "status": run.status,
        "winner": run.winner,
        "modes_completed": completed_modes,
        "total_modes": len(SUPPORTED_COMPARISON_MODES),
        "is_authoritative": run.is_authoritative,
    }


@router.get("/{comparison_id}/modes/{mode}", response_model=ModeComparisonResult)
async def get_mode_result(comparison_id: str, mode: str) -> ModeComparisonResult:
    """
    Retrieves detailed result for a specific mode within a comparison.
    Valid modes: 'no_coordination' | 'partial' | 'coordinated'
    """
    if mode not in SUPPORTED_COMPARISON_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode '{mode}'. Supported modes: {SUPPORTED_COMPARISON_MODES}",
        )

    run = default_comparison_repository.get(comparison_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison '{comparison_id}' not found",
        )

    if mode not in run.results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mode '{mode}' has not been evaluated in comparison '{comparison_id}'",
        )

    return run.results[mode]


@router.post("/{comparison_id}/run", response_model=ComparisonRun)
async def run_comparison(comparison_id: str) -> ComparisonRun:
    """
    Explicitly executes or re-runs a comparison run.
    """
    run = default_comparison_repository.get(comparison_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison '{comparison_id}' not found",
        )
    try:
        completed = await default_comparison_service.execute_comparison(comparison_id)
        return completed
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute comparison: {exc}",
        )

"""
REST API routes for Phase 14: Demo Path, Seeded Replay & Fallbacks.

Endpoints:
- POST /api/demo/launch: Execute a deterministic seeded demo comparison
- GET  /api/demo/runs: List all executed demo runs
- GET  /api/demo/runs/{demo_id}: Retrieve full demo run details
- POST /api/demo/runs/{demo_id}/restart: Prepare fresh restart with preserved/new seed
- POST /api/replays: Create a replay session from a simulation or comparison
- GET  /api/replays: List all recorded replay sessions
- GET  /api/replays/{replay_id}: Retrieve full replay event package
- GET  /api/replays/{replay_id}/seek: Retrieve playback snapshot at a specific tick
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.schemas.demo_models import (
    DemoLaunchRequest,
    DemoRun,
    ReplaySession,
    ReplayStateSnapshot,
)
from app.services.demo_service import (
    default_demo_repository,
    default_demo_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["demo_and_replay"])


class CreateReplayRequest(BaseModel):
    source_type: str = Field(..., description="'simulation' | 'comparison'")
    source_id: str = Field(..., description="Target simulation_id or comparison_id")
    seed: Optional[int] = Field(None, description="Optional seed metadata")


# ── Demo Path Endpoints ────────────────────────────────────────────────────────

@router.post("/demo/launch", response_model=DemoRun, status_code=status.HTTP_201_CREATED)
async def launch_demo(request: DemoLaunchRequest) -> DemoRun:
    """
    Executes a presentation-ready, deterministic 3-mode demo comparison.
    Guaranteed to run offline with zero external network or LLM dependency.
    """
    try:
        demo_run = await default_demo_service.launch_demo(request)
        return demo_run
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Demo execution failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo execution failed: {exc}",
        )


@router.get("/demo/runs", response_model=List[DemoRun])
async def list_demo_runs() -> List[DemoRun]:
    """
    Lists all executed demo sessions.
    """
    return default_demo_repository.list_demos()


@router.get("/demo/runs/{demo_id}", response_model=DemoRun)
async def get_demo_run(demo_id: str) -> DemoRun:
    """
    Retrieves full details and comparison outcomes for a demo session.
    """
    demo = default_demo_repository.get_demo(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo run '{demo_id}' not found",
        )
    return demo


@router.post("/demo/runs/{demo_id}/restart", response_model=DemoRun)
async def restart_demo(
    demo_id: str,
    new_seed: Optional[int] = Query(None, description="Optional new seed for subsequent run"),
) -> DemoRun:
    """
    Creates and launches a fresh demo run using the same scenario and either the same or new seed.
    Guarantees no state leakage from the previous run.
    """
    try:
        launch_req = default_demo_service.restart_demo(demo_id, new_seed=new_seed)
        new_run = await default_demo_service.launch_demo(launch_req)
        return new_run
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart demo: {exc}",
        )


# ── Replay Endpoints ──────────────────────────────────────────────────────────

@router.post("/replays", response_model=ReplaySession, status_code=status.HTTP_201_CREATED)
async def create_replay(request: CreateReplayRequest) -> ReplaySession:
    """
    Packages an existing simulation or comparison run into an immutable ReplaySession.
    """
    try:
        if request.source_type == "simulation":
            return default_demo_service.create_replay_from_simulation(
                simulation_id=request.source_id,
                seed=request.seed,
            )
        elif request.source_type == "comparison":
            return default_demo_service.create_replay_from_comparison(
                comparison_id=request.source_id,
                seed=request.seed,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source_type '{request.source_type}'. Expected 'simulation' or 'comparison'",
            )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to package replay: {exc}",
        )


@router.get("/replays", response_model=List[ReplaySession])
async def list_replays() -> List[ReplaySession]:
    """
    Lists all available replay recordings.
    """
    return default_demo_repository.list_replays()


@router.get("/replays/{replay_id}", response_model=ReplaySession)
async def get_replay(replay_id: str) -> ReplaySession:
    """
    Retrieves full chronological events and recorded outcome for a replay session.
    """
    replay = default_demo_repository.get_replay(replay_id)
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ReplaySession '{replay_id}' not found",
        )
    return replay


@router.get("/replays/{replay_id}/seek", response_model=ReplayStateSnapshot)
async def seek_replay(
    replay_id: str,
    to_tick: int = Query(..., ge=0, description="Target virtual tick"),
) -> ReplayStateSnapshot:
    """
    Retrieves a deterministic playback snapshot up to to_tick.
    """
    try:
        return default_demo_service.seek_replay(replay_id, to_tick)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

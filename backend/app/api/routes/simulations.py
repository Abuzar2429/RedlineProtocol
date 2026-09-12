"""
Simulation Engine REST API routes (Phase 3).
"""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.agents.coordinator_models import CoordinatorProposal
from app.schemas.simulation_models import (
    CreateSimulationRequest,
    SimulationEvent,
    SimulationState,
    SimulationStepResponse,
)
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository

router = APIRouter(prefix="/api/simulations", tags=["simulations"])


@router.post("", response_model=SimulationState, status_code=status.HTTP_201_CREATED)
async def create_simulation(request: CreateSimulationRequest) -> SimulationState:
    """
    Initializes a new deterministic crisis simulation session.
    """
    try:
        engine = SimulationEngine.create(
            scenario_id=request.scenario_id,
            mode=request.mode,
        )
        default_simulation_repository.save(engine)
        return engine.state
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario not found: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create simulation: {str(exc)}",
        )


@router.get("", response_model=List[SimulationState])
async def list_simulations() -> List[SimulationState]:
    """
    Lists all active or completed simulation sessions.
    """
    return default_simulation_repository.list_all()


@router.get("/{simulation_id}", response_model=SimulationState)
async def get_simulation(simulation_id: str) -> SimulationState:
    """
    Retrieves the current state of a specific simulation.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    return engine.state


@router.post("/{simulation_id}/start", response_model=SimulationState)
async def start_simulation(simulation_id: str) -> SimulationState:
    """
    Marks a simulation as RUNNING.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        return engine.start()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{simulation_id}/step", response_model=SimulationStepResponse)
async def step_simulation(simulation_id: str) -> SimulationStepResponse:
    """
    Executes a single deterministic simulation step (advancing ready events).
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        return engine.step()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{simulation_id}/run", response_model=SimulationState)
async def run_simulation(simulation_id: str) -> SimulationState:
    """
    Runs the simulation repeatedly until COMPLETED or loop limit reached.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        return engine.run_until_complete()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{simulation_id}/pause", response_model=SimulationState)
async def pause_simulation(simulation_id: str) -> SimulationState:
    """
    Pauses a running simulation.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        return engine.pause()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{simulation_id}/resume", response_model=SimulationState)
async def resume_simulation(simulation_id: str) -> SimulationState:
    """
    Resumes a paused simulation.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        return engine.resume()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/{simulation_id}/events", response_model=List[SimulationEvent])
async def get_simulation_events(simulation_id: str) -> List[SimulationEvent]:
    """
    Retrieves the complete chronologically ordered event history.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    return engine.state.event_history


# ── International Coordinator Routes — Phase 5 ─────────────────────────────────

@router.post("/{simulation_id}/coordinate", response_model=CoordinatorProposal)
async def trigger_coordination(simulation_id: str) -> CoordinatorProposal:
    """
    Invokes the International Coordinator Agent to synthesize current validated
    country positions and generate a structured proposal.
    Stores the proposal in the simulation state without modifying country state.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    from app.agents.coordinator_service import default_coordinator_service

    try:
        round_idx = len(engine.state.proposals) + 1
        proposal = await default_coordinator_service.request_coordination(
            state=engine.state,
            current_event=None,
            round_index=round_idx,
        )
        engine.state.proposals.append(proposal)
        engine.state.crisis_state.phase = "NEGOTIATION"
        return proposal
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coordinator proposal generation failed: {str(exc)}",
        )


@router.get("/{simulation_id}/proposals", response_model=List[CoordinatorProposal])
async def list_proposals(simulation_id: str) -> List[CoordinatorProposal]:
    """
    Lists all proposals produced by the International Coordinator for this simulation.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    return engine.state.proposals


@router.get("/{simulation_id}/proposals/{proposal_id}", response_model=CoordinatorProposal)
async def get_proposal(simulation_id: str, proposal_id: str) -> CoordinatorProposal:
    """
    Retrieves a specific proposal by its proposal_id.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    for p in engine.state.proposals:
        if p.proposal_id == proposal_id:
            return p
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Proposal '{proposal_id}' not found in simulation '{simulation_id}'",
    )


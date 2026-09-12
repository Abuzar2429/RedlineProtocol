"""
Simulation Engine REST API routes (Phase 3 & Phase 8).

Provides:
- Simulation lifecycle management (create, list, get, start, step, run, pause, resume, stop)
- Event history inspection with multi-attribute filtering
- Public country simulation state inspection
- International Coordinator proposal triggers
- Real-time event broadcasting to WebSocket subscribers
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.agents.coordinator_models import CoordinatorProposal
from app.schemas.simulation_models import (
    CreateSimulationRequest,
    SimulationEvent,
    SimulationState,
    SimulationStepResponse,
)
from app.schemas.websocket_models import PublicCountryState
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository
from app.services.websocket_manager import default_websocket_manager

router = APIRouter(prefix="/api/simulations", tags=["simulations"])


# ── Simulation Lifecycle Endpoints ─────────────────────────────────────────────

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


@router.get("/{simulation_id}/state", response_model=SimulationState)
async def get_simulation_state_alias(simulation_id: str) -> SimulationState:
    """
    Explicit endpoint alias for retrieving current simulation state.
    """
    return await get_simulation(simulation_id)


@router.post("/{simulation_id}/start", response_model=SimulationState)
async def start_simulation(simulation_id: str) -> SimulationState:
    """
    Marks a simulation as RUNNING and broadcasts SIMULATION_STARTED.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        state = engine.start()
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="SIMULATION_STARTED",
            payload={"status": state.status, "current_tick": state.current_tick},
            tick=state.current_tick,
            timestamp=state.current_time,
        )
        return state
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{simulation_id}/step", response_model=SimulationStepResponse)
async def step_simulation(simulation_id: str) -> SimulationStepResponse:
    """
    Executes a single deterministic simulation step (advancing ready events).
    Broadcasts each processed event and completion status to WebSocket subscribers.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        step_response = engine.step()

        # Broadcast each processed event in chronological order
        for event in step_response.events:
            await default_websocket_manager.broadcast_simulation_event(simulation_id, event)

        # Broadcast completion if reached
        if step_response.is_completed:
            await default_websocket_manager.broadcast_event(
                simulation_id=simulation_id,
                event_type="SIMULATION_COMPLETED",
                payload={"final_tick": step_response.current_tick, "status": "COMPLETED"},
                tick=step_response.current_tick,
                timestamp=step_response.current_time,
                category="complete",
            )

        return step_response
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{simulation_id}/run", response_model=SimulationState)
async def run_simulation(
    simulation_id: str,
    max_ticks: Optional[int] = Query(None, ge=1, le=240, description="Optional tick limit for run"),
) -> SimulationState:
    """
    Runs the simulation repeatedly until COMPLETED or loop limit reached.
    Broadcasts all generated events in real-time.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    try:
        limit = max_ticks or engine.max_ticks
        if engine.state.status == "CREATED":
            engine.start()
            await default_websocket_manager.broadcast_event(
                simulation_id=simulation_id,
                event_type="SIMULATION_STARTED",
                payload={"status": "RUNNING"},
                tick=engine.state.current_tick,
                timestamp=engine.state.current_time,
            )

        while engine.state.status == "RUNNING" and engine.clock.current_tick < limit:
            step_res = engine.step()
            for ev in step_res.events:
                await default_websocket_manager.broadcast_simulation_event(simulation_id, ev)
            if step_res.is_completed:
                break

        engine.state.status = "COMPLETED"
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="SIMULATION_COMPLETED",
            payload={"final_tick": engine.state.current_tick, "status": "COMPLETED"},
            tick=engine.state.current_tick,
            timestamp=engine.state.current_time,
            category="complete",
        )
        return engine.state
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
        state = engine.pause()
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="SIMULATION_PAUSED",
            payload={"status": "PAUSED", "current_tick": state.current_tick},
            tick=state.current_tick,
            timestamp=state.current_time,
        )
        return state
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
        state = engine.resume()
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="SIMULATION_RESUMED",
            payload={"status": "RUNNING", "current_tick": state.current_tick},
            tick=state.current_tick,
            timestamp=state.current_time,
        )
        return state
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{simulation_id}/stop", response_model=SimulationState)
async def stop_simulation(simulation_id: str) -> SimulationState:
    """
    Explicitly terminates/completes a simulation session.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    engine.state.status = "COMPLETED"
    await default_websocket_manager.broadcast_event(
        simulation_id=simulation_id,
        event_type="SIMULATION_STOPPED",
        payload={"status": "COMPLETED", "final_tick": engine.state.current_tick},
        tick=engine.state.current_tick,
        timestamp=engine.state.current_time,
        category="complete",
    )
    return engine.state


# ── Event History with Query Filtering ─────────────────────────────────────────

@router.get("/{simulation_id}/events", response_model=List[SimulationEvent])
async def get_simulation_events(
    simulation_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    country_id: Optional[str] = Query(None, description="Filter by affected country ID"),
    start_tick: Optional[int] = Query(None, ge=0, description="Earliest tick inclusive"),
    end_tick: Optional[int] = Query(None, ge=0, description="Latest tick inclusive"),
) -> List[SimulationEvent]:
    """
    Retrieves the chronologically ordered event history, with optional filtering.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    events = engine.state.event_history
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    if country_id:
        events = [e for e in events if country_id in e.affected_countries]
    if start_tick is not None:
        events = [e for e in events if e.tick >= start_tick]
    if end_tick is not None:
        events = [e for e in events if e.tick <= end_tick]

    return events


# ── Public Country State Endpoints ─────────────────────────────────────────────

@router.get("/{simulation_id}/countries", response_model=List[PublicCountryState])
async def list_simulation_countries(simulation_id: str) -> List[PublicCountryState]:
    """
    Retrieves public simulation states for all countries in this simulation.
    Excludes internal private reasoning and secrets.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    result = []
    for cid, cs in engine.state.countries.items():
        result.append(
            PublicCountryState(
                country_id=cid,
                name=cs.name,
                status=cs.status,
                aware=cs.aware,
                information_completeness=round(cs.information_completeness, 2),
                current_action=cs.current_action,
                coordination_status=cs.coordination_status or "Independent",
                decision_count=cs.decision_count,
                last_updated_tick=cs.last_updated_tick,
            )
        )
    return result


@router.get("/{simulation_id}/countries/{country_id}", response_model=PublicCountryState)
async def get_simulation_country(simulation_id: str, country_id: str) -> PublicCountryState:
    """
    Retrieves the public simulation state for a specific country in this simulation.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    if country_id not in engine.state.countries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country '{country_id}' not found in simulation '{simulation_id}'",
        )

    cs = engine.state.countries[country_id]
    return PublicCountryState(
        country_id=country_id,
        name=cs.name,
        status=cs.status,
        aware=cs.aware,
        information_completeness=round(cs.information_completeness, 2),
        current_action=cs.current_action,
        coordination_status=cs.coordination_status or "Independent",
        decision_count=cs.decision_count,
        last_updated_tick=cs.last_updated_tick,
    )


# ── International Coordinator Routes — Phase 5 ─────────────────────────────────

@router.post("/{simulation_id}/coordinate", response_model=CoordinatorProposal)
async def trigger_coordination(simulation_id: str) -> CoordinatorProposal:
    """
    Invokes the International Coordinator Agent to synthesize current validated
    country positions and generate a structured proposal.
    Broadcasts COORDINATOR_PROPOSAL to WebSocket subscribers.
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

        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="COORDINATOR_PROPOSAL",
            payload={
                "proposal_id": proposal.proposal_id,
                "round": getattr(proposal, "round", 1),
                "title": getattr(proposal, "title", ""),
                "summary": getattr(proposal, "summary", ""),
                "items": getattr(proposal, "items", []),
                "supporting_countries": proposal.supporting_countries,
                "opposing_countries": getattr(proposal, "opposing_countries", []),
            },
            tick=engine.state.current_tick,
            timestamp=engine.state.current_time,
            category="negotiation",
        )
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

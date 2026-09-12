"""
Negotiation and Voting REST API endpoints (Phase 6).
Provides endpoints to trigger negotiations, advance rounds, inspect votes, and retrieve outcomes.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.negotiation.negotiation_service import default_negotiation_service
from app.schemas.negotiation_models import (
    NegotiationOutcome,
    NegotiationRound,
    NegotiationSession,
    Vote,
    VoteType,
)
from app.services.simulation.repository import default_simulation_repository
from app.services.websocket_manager import default_websocket_manager

router = APIRouter(prefix="/api/simulations", tags=["negotiations"])


class SubmitVoteRequest(BaseModel):
    country_id: str = Field(..., description="Country ID voting")
    vote: VoteType = Field(..., description="'Approve' | 'Reject' | 'Undecided'")
    rationale: str = Field(..., description="Justification")
    conditions_requested: List[str] = Field(default_factory=list)
    objections_raised: List[str] = Field(default_factory=list)


class StartNegotiationRequest(BaseModel):
    max_rounds: int = Field(3, ge=1, le=5)
    proposal_id: Optional[str] = None


@router.post("/{simulation_id}/negotiate", response_model=NegotiationOutcome)
async def run_negotiation(
    simulation_id: str,
    request: Optional[StartNegotiationRequest] = None,
) -> NegotiationOutcome:
    """
    Initiates and runs a complete negotiation session for the latest proposal,
    executing rounds until an agreement, deadlock, or max rounds is reached.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )

    max_rounds = request.max_rounds if request else 3
    proposal = None
    if request and request.proposal_id:
        proposal = next((p for p in engine.state.proposals if p.proposal_id == request.proposal_id), None)
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal '{request.proposal_id}' not found",
            )
    elif not engine.state.proposals:
        # If no proposal exists yet, generate one first via Coordinator
        from app.agents.coordinator_service import default_coordinator_service
        try:
            round_idx = len(engine.state.proposals) + 1
            proposal = await default_coordinator_service.request_coordination(
                state=engine.state,
                round_index=round_idx,
            )
            engine.state.proposals.append(proposal)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate coordinator proposal: {exc}",
            )

    try:
        session = default_negotiation_service.start_negotiation(
            state=engine.state,
            proposal=proposal,
            max_rounds=max_rounds,
        )
        active_prop_id = proposal.proposal_id if proposal else (
            session.proposal_versions[0].proposal_id if session.proposal_versions else "unknown"
        )
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="NEGOTIATION_STARTED",
            payload={"session_id": session.negotiation_id, "proposal_id": active_prop_id},
            tick=engine.state.current_tick,
            timestamp=engine.state.current_time,
            category="negotiation",
        )
        outcome = default_negotiation_service.run_full_negotiation(session, engine.state)
        engine.state.negotiations.append(session)

        for r in session.rounds:
            v_res = r.voting_result
            r_tick = r.completed_at_tick if r.completed_at_tick is not None else r.started_at_tick
            await default_websocket_manager.broadcast_event(
                simulation_id=simulation_id,
                event_type="NEGOTIATION_ROUND_COMPLETED",
                payload={
                    "session_id": session.negotiation_id,
                    "round_number": r.round_number,
                    "approvals": v_res.votes_for if v_res else 0,
                    "rejections": v_res.votes_against if v_res else 0,
                    "undecided": v_res.abstentions if v_res else 0,
                    "passed": v_res.passed if v_res else False,
                },
                tick=r_tick,
                timestamp=f"T+{r_tick:02d}",
                category="negotiation",
            )

        coord_ratio = len(outcome.supporting_countries) / max(1, len(engine.state.countries))
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="NEGOTIATION_OUTCOME",
            payload={
                "session_id": session.negotiation_id,
                "agreement_reached": outcome.agreement_reached,
                "final_status": outcome.final_status,
                "coordination_score": round(coord_ratio, 2),
                "supporting_countries": outcome.supporting_countries,
                "unresolved_issues": outcome.unresolved_issues,
            },
            tick=engine.state.current_tick,
            timestamp=engine.state.current_time,
            category="negotiation",
        )
        return outcome
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Negotiation failed: {str(exc)}",
        )


@router.get("/{simulation_id}/negotiations", response_model=List[NegotiationSession])
async def list_negotiations(simulation_id: str) -> List[NegotiationSession]:
    """
    Lists all negotiation sessions recorded for this simulation.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    return engine.state.negotiations


@router.get("/{simulation_id}/negotiations/{negotiation_id}", response_model=NegotiationSession)
async def get_negotiation(simulation_id: str, negotiation_id: str) -> NegotiationSession:
    """
    Retrieves full details and round history for a specific negotiation session.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    for neg in engine.state.negotiations:
        if neg.negotiation_id == negotiation_id:
            return neg
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Negotiation session '{negotiation_id}' not found",
    )


@router.post("/{simulation_id}/negotiations/{negotiation_id}/advance", response_model=NegotiationRound)
async def advance_negotiation_round(simulation_id: str, negotiation_id: str) -> NegotiationRound:
    """
    Advances a negotiation session by a single discrete round.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    target_session = next((s for s in engine.state.negotiations if s.negotiation_id == negotiation_id), None)
    if not target_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation session '{negotiation_id}' not found",
        )
    try:
        round_rec = default_negotiation_service.execute_round(target_session, engine.state)
        v_res = round_rec.voting_result
        r_tick = round_rec.completed_at_tick if round_rec.completed_at_tick is not None else round_rec.started_at_tick
        await default_websocket_manager.broadcast_event(
            simulation_id=simulation_id,
            event_type="NEGOTIATION_ROUND_COMPLETED",
            payload={
                "session_id": target_session.negotiation_id,
                "round_number": round_rec.round_number,
                "approvals": v_res.votes_for if v_res else 0,
                "rejections": v_res.votes_against if v_res else 0,
                "undecided": v_res.abstentions if v_res else 0,
                "passed": v_res.passed if v_res else False,
            },
            tick=r_tick,
            timestamp=f"T+{r_tick:02d}",
            category="negotiation",
        )
        if target_session.outcome:
            await default_websocket_manager.broadcast_event(
                simulation_id=simulation_id,
                event_type="NEGOTIATION_OUTCOME",
                payload={
                    "session_id": target_session.negotiation_id,
                    "agreement_reached": target_session.outcome.agreement_reached,
                    "final_status": target_session.outcome.final_status,
                    "coordination_score": round(len(target_session.outcome.supporting_countries) / max(1, len(engine.state.countries)), 2),
                    "supporting_countries": target_session.outcome.supporting_countries,
                },
                tick=engine.state.current_tick,
                timestamp=engine.state.current_time,
                category="negotiation",
            )
        return round_rec
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/{simulation_id}/negotiations/{negotiation_id}/outcome", response_model=NegotiationOutcome)
async def get_negotiation_outcome(simulation_id: str, negotiation_id: str) -> NegotiationOutcome:
    """
    Retrieves the final structured outcome for a negotiation session.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found",
        )
    target_session = next((s for s in engine.state.negotiations if s.negotiation_id == negotiation_id), None)
    if not target_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation session '{negotiation_id}' not found",
        )
    if not target_session.outcome:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Negotiation session '{negotiation_id}' is still in progress (status '{target_session.status}')",
        )
    return target_session.outcome

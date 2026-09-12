"""
Negotiation Session Manager and State Machine (Phase 6).
Maintains strict state transitions, orchestrates multi-round voting,
aggregates unresolved issues, and enforces max round limits (default 3).
"""
import logging
from typing import Dict, List, Optional

from app.negotiation.position_service import CountryPositionEvaluator
from app.negotiation.voting_engine import get_voting_rule
from app.schemas.coordinator_models import CoordinatorProposal
from app.schemas.data_models import CountryData
from app.schemas.negotiation_models import (
    NegotiationOutcome,
    NegotiationRound,
    NegotiationSession,
    NegotiationStatus,
    ProposalVersion,
    Vote,
    VotingResult,
)
from app.schemas.simulation_models import DecisionRecord, SimulationState

logger = logging.getLogger(__name__)

# Valid state machine transitions
ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "PROPOSED": ["NEGOTIATION_OPEN", "FAILED", "BREAKDOWN"],
    "NEGOTIATION_OPEN": ["ROUND_ACTIVE", "FAILED", "NO_QUORUM"],
    "ROUND_ACTIVE": ["POSITIONS_COLLECTED", "VOTING", "FAILED"],
    "POSITIONS_COLLECTED": ["VOTING", "FAILED"],
    "VOTING": ["VOTE_EVALUATED", "FAILED"],
    "VOTE_EVALUATED": [
        "ACCEPTED",
        "PARTIAL_AGREEMENT",
        "REVISION_REQUIRED",
        "FAILED",
        "BREAKDOWN",
        "MAX_ROUNDS_REACHED",
        "NO_QUORUM",
    ],
    "REVISION_REQUIRED": ["ROUND_ACTIVE", "FAILED", "MAX_ROUNDS_REACHED"],
    "ACCEPTED": [],  # Terminal state
    "PARTIAL_AGREEMENT": [],  # Terminal state
    "FAILED": [],  # Terminal state
    "BREAKDOWN": [],  # Terminal state
    "MAX_ROUNDS_REACHED": [],  # Terminal state
    "NO_QUORUM": [],  # Terminal state
}


class NegotiationSessionManager:
    """
    State machine and lifecycle controller for a NegotiationSession.
    """

    @classmethod
    def create_session(
        cls,
        state: SimulationState,
        initial_proposal: CoordinatorProposal,
        max_rounds: int = 3,
    ) -> NegotiationSession:
        """
        Initializes a NegotiationSession from a CoordinatorProposal (Phase 5).
        """
        proposal_id = initial_proposal.proposal_id
        session_id = f"neg_{state.simulation_id[:8]}_t{state.current_tick:02d}"

        v1 = ProposalVersion(
            version=1,
            proposal_id=proposal_id,
            title=initial_proposal.title,
            summary=initial_proposal.summary,
            items=list(initial_proposal.items),
            rationale=initial_proposal.rationale,
            revision_reason="Initial multilateral proposal from International Coordinator",
            unresolved_issues=list(initial_proposal.unresolved_issues),
            created_at_tick=state.current_tick,
            source=initial_proposal.source,
        )

        eligible = sorted(state.countries.keys())

        session = NegotiationSession(
            negotiation_id=session_id,
            simulation_id=state.simulation_id,
            scenario_id=state.scenario_id,
            coordination_mode=state.mode,
            status="PROPOSED",
            current_round=1,
            max_rounds=max_rounds,
            participating_countries=eligible,
            proposal_versions=[v1],
            rounds=[],
            outcome=None,
            created_at_tick=state.current_tick,
        )
        return session

    @classmethod
    def transition(cls, session: NegotiationSession, new_status: NegotiationStatus) -> None:
        """
        Enforces deterministic state transitions according to the state machine.
        """
        current = session.status
        allowed = ALLOWED_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid negotiation state transition: '{current}' -> '{new_status}'. Allowed: {allowed}"
            )
        session.status = new_status
        logger.debug("NegotiationSession[%s] status -> %s", session.negotiation_id, new_status)

    @classmethod
    def run_round(
        cls,
        session: NegotiationSession,
        state: SimulationState,
        countries_map: Dict[str, CountryData],
        manual_votes: Optional[Dict[str, Vote]] = None,
    ) -> NegotiationRound:
        """
        Executes a single negotiation round deterministically:
        1. Transitions state through ROUND_ACTIVE -> POSITIONS_COLLECTED -> VOTING.
        2. Gathers and validates votes from all eligible countries.
        3. Evaluates votes using the mode's voting strategy.
        4. Checks termination conditions (pass, stable deadlock, or max rounds).
        """
        if session.status in (
            "ACCEPTED",
            "PARTIAL_AGREEMENT",
            "FAILED",
            "BREAKDOWN",
            "MAX_ROUNDS_REACHED",
            "NO_QUORUM",
        ):
            raise ValueError(f"Negotiation session '{session.negotiation_id}' has already concluded with status '{session.status}'.")

        # Ensure active state
        if session.status in ("PROPOSED", "REVISION_REQUIRED"):
            cls.transition(session, "NEGOTIATION_OPEN" if session.status == "PROPOSED" else "ROUND_ACTIVE")

        if session.status == "NEGOTIATION_OPEN":
            cls.transition(session, "ROUND_ACTIVE")

        current_ver = session.proposal_versions[-1]
        round_num = session.current_round

        # Extract latest decisions per country
        latest_decisions: Dict[str, DecisionRecord] = {}
        for d in state.decisions:
            if d.tick <= state.current_tick:
                latest_decisions[d.country_id] = d

        # Step 2: Collect & Validate Votes
        cls.transition(session, "POSITIONS_COLLECTED")
        cls.transition(session, "VOTING")

        votes: Dict[str, Vote] = {}
        for country_id in session.participating_countries:
            if manual_votes and country_id in manual_votes:
                v = manual_votes[country_id]
                # Validate manual vote integrity
                if v.country_id != country_id or v.round != round_num:
                    raise ValueError(f"Invalid manual vote metadata for {country_id}")
                votes[country_id] = v
            else:
                c_data = countries_map.get(country_id)
                c_state = state.countries.get(country_id)
                if not c_data or not c_state:
                    continue
                v = CountryPositionEvaluator.evaluate_vote(
                    country=c_data,
                    country_state=c_state,
                    proposal_version=current_ver,
                    round_number=round_num,
                    latest_decision=latest_decisions.get(country_id),
                    tick=state.current_tick,
                )
                votes[country_id] = v

        # Step 3: Evaluate Voting Result
        voting_rule = get_voting_rule(session.coordination_mode)
        result: VotingResult = voting_rule.evaluate(
            round_num=round_num,
            proposal_version=current_ver,
            votes=votes,
            eligible_countries=session.participating_countries,
        )

        cls.transition(session, "VOTE_EVALUATED")

        # Collect unresolved issues from this round's objections & conditions
        unresolved: List[str] = list(current_ver.unresolved_issues)
        for v in votes.values():
            if v.vote in ("Reject", "Undecided"):
                for obj in v.objections_raised:
                    if obj not in unresolved:
                        unresolved.append(obj)
                for cond in v.conditions_requested:
                    if cond not in unresolved:
                        unresolved.append(cond)

        round_record = NegotiationRound(
            round_number=round_num,
            proposal_version=current_ver,
            votes=votes,
            voting_result=result,
            unresolved_issues=unresolved[:10],
            status="COMPLETED",
            started_at_tick=state.current_tick,
            completed_at_tick=state.current_tick,
        )
        session.rounds.append(round_record)

        # Step 4: Handle Outcome / Progression
        if result.passed:
            final_status = "ACCEPTED" if session.coordination_mode == "coordinated" else "PARTIAL_AGREEMENT"
            cls.transition(session, final_status)
            session.outcome = NegotiationOutcome(
                negotiation_id=session.negotiation_id,
                simulation_id=session.simulation_id,
                coordination_mode=session.coordination_mode,
                final_status=final_status,
                agreement_reached=True,
                rounds_completed=round_num,
                final_proposal_version=current_ver.version,
                final_proposal=current_ver,
                final_vote_result=result,
                supporting_countries=result.approving_countries,
                opposing_countries=result.opposing_countries,
                abstaining_countries=result.abstaining_countries,
                unresolved_issues=unresolved[:5],
                failure_reason=None,
                completed_at_tick=state.current_tick,
            )
            return round_record

        # Check for No Quorum
        if result.status == "NO_QUORUM":
            cls.transition(session, "NO_QUORUM")
            session.outcome = NegotiationOutcome(
                negotiation_id=session.negotiation_id,
                simulation_id=session.simulation_id,
                coordination_mode=session.coordination_mode,
                final_status="NO_QUORUM",
                agreement_reached=False,
                rounds_completed=round_num,
                final_proposal_version=current_ver.version,
                final_proposal=current_ver,
                final_vote_result=result,
                supporting_countries=result.approving_countries,
                opposing_countries=result.opposing_countries,
                abstaining_countries=result.abstaining_countries,
                unresolved_issues=unresolved[:5],
                failure_reason=result.failure_reason or "Quorum not met",
                completed_at_tick=state.current_tick,
            )
            return round_record

        # Check if max rounds reached
        if round_num >= session.max_rounds:
            cls.transition(session, "MAX_ROUNDS_REACHED")
            session.outcome = NegotiationOutcome(
                negotiation_id=session.negotiation_id,
                simulation_id=session.simulation_id,
                coordination_mode=session.coordination_mode,
                final_status="MAX_ROUNDS_REACHED",
                agreement_reached=False,
                rounds_completed=round_num,
                final_proposal_version=current_ver.version,
                final_proposal=current_ver,
                final_vote_result=result,
                supporting_countries=result.approving_countries,
                opposing_countries=result.opposing_countries,
                abstaining_countries=result.abstaining_countries,
                unresolved_issues=unresolved[:5],
                failure_reason=f"Maximum rounds ({session.max_rounds}) reached without consensus: {result.failure_reason}",
                completed_at_tick=state.current_tick,
            )
            return round_record

        # Check for Stable Deadlock (rules.md: vote counts unchanged between rounds)
        if len(session.rounds) >= 2:
            prev_res = session.rounds[-2].voting_result
            if (
                prev_res
                and prev_res.votes_for == result.votes_for
                and prev_res.votes_against == result.votes_against
                and prev_res.abstentions == result.abstentions
            ):
                cls.transition(session, "BREAKDOWN")
                session.outcome = NegotiationOutcome(
                    negotiation_id=session.negotiation_id,
                    simulation_id=session.simulation_id,
                    coordination_mode=session.coordination_mode,
                    final_status="BREAKDOWN",
                    agreement_reached=False,
                    rounds_completed=round_num,
                    final_proposal_version=current_ver.version,
                    final_proposal=current_ver,
                    final_vote_result=result,
                    supporting_countries=result.approving_countries,
                    opposing_countries=result.opposing_countries,
                    abstaining_countries=result.abstaining_countries,
                    unresolved_issues=unresolved[:5],
                    failure_reason="Deadlock: vote counts remained stable without progress across rounds.",
                    completed_at_tick=state.current_tick,
                )
                return round_record

        # Otherwise, initiate revision round
        cls.transition(session, "REVISION_REQUIRED")
        next_ver_num = current_ver.version + 1
        revised_items = list(current_ver.items)
        if unresolved:
            revised_items.append(f"Incorporate compromise protocol on '{unresolved[0][:60]}'")

        revised_proposal = ProposalVersion(
            version=next_ver_num,
            proposal_id=current_ver.proposal_id,
            title=f"{current_ver.title} (Rev. {next_ver_num})",
            summary=f"Revised multilateral terms addressing Round {round_num} objections and reservations.",
            items=revised_items,
            rationale=f"Compromise draft balancing dissenting sovereignty concerns from Round {round_num}.",
            revision_reason=f"Addressing objections: {', '.join(unresolved[:2])}",
            unresolved_issues=unresolved[:5],
            created_at_tick=state.current_tick,
            source="deterministic_fallback",
        )
        session.proposal_versions.append(revised_proposal)
        session.current_round += 1

        return round_record

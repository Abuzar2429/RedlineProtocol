"""
Scoring Snapshot Builder for AI Governance Crisis Simulator (Phase 7).

Extracts an immutable ScoringInputSnapshot from the authoritative SimulationState
to guarantee reproducible, deterministic scoring calculations.
"""
from typing import Dict, List, Optional

from app.schemas.scoring_models import ScoringInputSnapshot
from app.schemas.simulation_models import SimulationState
from app.scoring.metrics import DEFAULT_ACTION_RISK_REDUCTIONS


class ScoringSnapshotBuilder:
    """
    Transforms a mutable SimulationState into an immutable ScoringInputSnapshot.
    """

    @classmethod
    def from_simulation_state(cls, state: SimulationState) -> ScoringInputSnapshot:
        """
        Builds the snapshot from the authoritative simulation state.
        """
        sim_id = state.simulation_id
        scenario_id = state.scenario_id
        mode = state.mode
        final_tick = state.current_tick
        
        # 1. Determine detection tick
        detection_tick = 0
        for ev in state.event_history:
            if ev.event_type == "CRISIS_TRIGGERED":
                detection_tick = ev.tick
                break
            if ev.payload.get("timeline_type") == "detection":
                detection_tick = ev.tick
                break
                
        # 2. Extract unique actions committed
        actions_seen = []
        for dec in state.decisions:
            if dec.action_id and dec.action_id not in actions_seen:
                actions_seen.append(dec.action_id)
                
        # Also check country current_action if recorded
        for c_state in state.countries.values():
            if c_state.current_action and c_state.current_action not in actions_seen:
                # If current_action is an action_id, include it
                if c_state.current_action in DEFAULT_ACTION_RISK_REDUCTIONS:
                    actions_seen.append(c_state.current_action)

        # 3. Determine coordinated action tick and status
        coordinated_action_tick: Optional[int] = None
        coordinated_occurred = False
        final_agreement_reached = False
        final_negotiation_status: Optional[str] = None
        
        # Check negotiation history
        if state.negotiations:
            latest_session = state.negotiations[-1]
            final_negotiation_status = latest_session.status
            if latest_session.outcome and latest_session.outcome.agreement_reached:
                final_agreement_reached = True
                coordinated_occurred = True
                
            # Search event history for NEGOTIATION_PASSED event
            for ev in state.event_history:
                if ev.event_type == "NEGOTIATION_PASSED":
                    coordinated_action_tick = ev.tick
                    coordinated_occurred = True
                    final_agreement_reached = True
                    break

            # If no event found but session passed, use round timestamp or current tick
            if coordinated_occurred and coordinated_action_tick is None:
                if latest_session.rounds:
                    coordinated_action_tick = latest_session.rounds[-1].timestamp_tick
                else:
                    coordinated_action_tick = final_tick

        # Fallback check: look for ratification action in decisions
        if coordinated_action_tick is None:
            for dec in state.decisions:
                if "ratif" in dec.action_id.lower() or "containment" in dec.action_id.lower():
                    coordinated_action_tick = dec.tick
                    coordinated_occurred = True
                    break

        # 4. Count and partition countries
        total_countries = len(state.countries) if state.countries else 15
        
        # Determine approving, opposing, undecided from negotiation if available
        approving_countries: List[str] = []
        opposing_countries: List[str] = []
        undecided_countries: List[str] = []
        unresolved_issues_raw: List[str] = []
        
        if state.negotiations:
            latest_session = state.negotiations[-1]
            if latest_session.outcome and latest_session.outcome.unresolved_issues:
                unresolved_issues_raw.extend(latest_session.outcome.unresolved_issues)
            for r in latest_session.rounds:
                if r.unresolved_issues:
                    unresolved_issues_raw.extend(r.unresolved_issues)
            
            if latest_session.outcome:
                approving_countries = list(latest_session.outcome.supporting_countries)
                opposing_countries = list(latest_session.outcome.opposing_countries)
                undecided_countries = list(
                    getattr(latest_session.outcome, "abstaining_countries", None)
                    or getattr(latest_session.outcome, "undecided_countries", [])
                )

            elif latest_session.rounds:
                latest_round = latest_session.rounds[-1]
                votes_iterable = latest_round.votes.values() if isinstance(latest_round.votes, dict) else latest_round.votes
                for v in votes_iterable:
                    if v.vote == "Approve":
                        approving_countries.append(v.country_id)
                    elif v.vote == "Reject":
                        opposing_countries.append(v.country_id)
                    else:
                        undecided_countries.append(v.country_id)

        elif state.proposals:
            # If proposals exist but negotiation didn't run
            latest_prop = state.proposals[-1]
            unresolved_issues_raw.extend(latest_prop.unresolved_issues)
            approving_countries = list(latest_prop.supporting_countries)
            opposing_countries = list(latest_prop.opposing_countries)
        else:
            # Mode-based fallback (e.g. no coordination)
            for cid, c_state in state.countries.items():
                if c_state.status == "Coordinating":
                    approving_countries.append(cid)
                elif c_state.status in ("Investigating", "Notified"):
                    undecided_countries.append(cid)
                else:
                    opposing_countries.append(cid)

        # Deduplicate country lists
        approving_countries = list(dict.fromkeys(approving_countries))
        opposing_countries = list(dict.fromkeys(opposing_countries))
        undecided_countries = list(dict.fromkeys(undecided_countries))
        
        participating_countries = list(dict.fromkeys(
            approving_countries + opposing_countries + undecided_countries
        ))

        # Negotiation counts
        neg_sessions_count = len(state.negotiations)
        neg_rounds_count = sum(len(s.rounds) for s in state.negotiations)

        return ScoringInputSnapshot(
            simulation_id=sim_id,
            scenario_id=scenario_id,
            mode=mode,
            start_tick=detection_tick,
            final_tick=final_tick,
            simulation_status=state.status,
            crisis_phase=state.crisis_state.phase,
            unique_actions_taken=actions_seen,
            action_risk_reductions=DEFAULT_ACTION_RISK_REDUCTIONS,
            detection_tick=detection_tick,
            coordinated_action_tick=coordinated_action_tick,
            coordinated_action_occurred=coordinated_occurred,
            total_countries=total_countries,
            participating_countries=participating_countries,
            approving_countries=approving_countries,
            opposing_countries=opposing_countries,
            undecided_countries=undecided_countries,
            negotiation_sessions_count=neg_sessions_count,
            negotiation_rounds_count=neg_rounds_count,
            final_agreement_reached=final_agreement_reached,
            final_negotiation_status=final_negotiation_status,
            unresolved_issues_raw=unresolved_issues_raw,
        )

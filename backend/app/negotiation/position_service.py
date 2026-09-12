"""
Country Position Evaluator for Phase 6.
Deterministically derives country voting positions (Approve, Reject, Undecided)
based on country profile, awareness state, strategic priorities, and proposal terms.
"""
from typing import Dict, List, Optional

from app.schemas.data_models import CountryData
from app.schemas.negotiation_models import ProposalVersion, Vote, VoteType
from app.schemas.simulation_models import CountrySimulationState, DecisionRecord


class CountryPositionEvaluator:
    """
    Evaluates country stances and constructs strictly validated Vote records.
    100% deterministic and reproducible based on national strategic doctrine.
    """

    @classmethod
    def evaluate_vote(
        cls,
        country: CountryData,
        country_state: CountrySimulationState,
        proposal_version: ProposalVersion,
        round_number: int,
        latest_decision: Optional[DecisionRecord] = None,
        tick: int = 0,
    ) -> Vote:
        vote_id = f"vote_{country.id}_r{round_number}_v{proposal_version.version}"

        # 1. Unaware countries must abstain (Undecided)
        if country_state.status == "Unaware":
            return Vote(
                vote_id=vote_id,
                country_id=country.id,
                round=round_number,
                proposal_id=proposal_version.proposal_id,
                proposal_version=proposal_version.version,
                vote="Undecided",
                rationale="National intelligence agencies have not confirmed crisis telemetry; country abstains.",
                conditions_requested=[],
                objections_raised=[],
                created_at_tick=tick,
            )

        # 2. Extract coordination willingness
        if latest_decision and latest_decision.willingness_to_coordinate is not None:
            willingness = latest_decision.willingness_to_coordinate
        else:
            w_map = {"high": 0.85, "moderate": 0.55, "low": 0.25}
            willingness = w_map.get(country.coordination_willingness.lower(), 0.50)

        # 3. Derive vote from willingness & doctrine
        # High coordination willingness -> Approve
        if willingness >= 0.60:
            vote_val: VoteType = "Approve"
            rationale = (
                f"As policy authority for {country.name}, national strategic doctrine endorses "
                f"'{proposal_version.title}' to safeguard regional stability and contain systemic risk."
            )
            conditions = []
            objections = []

        # Low coordination willingness -> Reject
        elif willingness < 0.40:
            vote_val = "Reject"
            rationale = (
                f"{country.name} rejects proposal version {proposal_version.version}. Mandatory external "
                f"oversight conflicts with sovereign defense doctrine and proprietary safety boundaries."
            )
            conditions = [
                "Demands sovereign exemption for domestic critical infrastructure compute.",
            ]
            objections = [
                "Inspection protocol access boundaries violate sovereign technological autonomy.",
                "Lack of indemnification for algorithmic suspension losses.",
            ]

        # Moderate coordination willingness -> Undecided (conditional reservation)
        else:
            vote_val = "Undecided"
            rationale = (
                f"{country.name} expresses conditional reservations regarding proposal version "
                f"{proposal_version.version}. Support contingent on verification transparency and multilateral parity."
            )
            conditions = [
                "Requires neutral multilateral arbitration for contested compliance claims.",
                "Requests reciprocal evidence sharing from all frontier deployment nations.",
            ]
            objections = [
                "Timeline for compliance audits requires extension to avoid domestic market disruption.",
            ]

        return Vote(
            vote_id=vote_id,
            country_id=country.id,
            round=round_number,
            proposal_id=proposal_version.proposal_id,
            proposal_version=proposal_version.version,
            vote=vote_val,
            rationale=rationale,
            conditions_requested=conditions,
            objections_raised=objections,
            created_at_tick=tick,
        )

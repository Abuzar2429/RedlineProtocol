"""
Deterministic Voting Engine implementing strategy pattern for the three coordination modes:
1. NoCoordinationVotingRule ("no_coordination")
2. PartialCoordinationVotingRule ("partial")
3. CoordinatedVotingRule ("coordinated")
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.schemas.negotiation_models import ProposalVersion, Vote, VotingResult
from app.schemas.simulation_models import SimulationMode


class BaseVotingRule(ABC):
    """
    Abstract base strategy for deterministic voting evaluation.
    """

    def __init__(self, mode: SimulationMode):
        self.mode = mode

    @abstractmethod
    def evaluate(
        self,
        round_num: int,
        proposal_version: ProposalVersion,
        votes: Dict[str, Vote],
        eligible_countries: List[str],
    ) -> VotingResult:
        """
        Deterministically evaluates votes cast in a round against the mode's rules.
        """
        pass

    def _tally_votes(
        self,
        votes: Dict[str, Vote],
        eligible_countries: List[str],
    ) -> tuple[int, int, int, List[str], List[str], List[str]]:
        """
        Deterministically tallies votes into Approve, Reject, and Undecided buckets,
        ignoring or discarding any votes from ineligible countries.
        """
        eligible_set = set(eligible_countries)
        approving: List[str] = []
        opposing: List[str] = []
        abstaining: List[str] = []

        # Sort keys deterministically by country_id
        for cid in sorted(votes.keys()):
            if cid not in eligible_set:
                continue  # Reject ineligible country votes from tally
            v = votes[cid]
            if v.vote == "Approve":
                approving.append(cid)
            elif v.vote == "Reject":
                opposing.append(cid)
            else:
                abstaining.append(cid)

        return (
            len(approving),
            len(opposing),
            len(abstaining),
            approving,
            opposing,
            abstaining,
        )


class NoCoordinationVotingRule(BaseVotingRule):
    """
    Mode: 'no_coordination'
    Sovereign states act completely unilaterally. Multilateral coordination is disabled.
    Proposals always fail immediately with zero quorum and zero approval.
    """

    def __init__(self):
        super().__init__("no_coordination")

    def evaluate(
        self,
        round_num: int,
        proposal_version: ProposalVersion,
        votes: Dict[str, Vote],
        eligible_countries: List[str],
    ) -> VotingResult:
        n_for, n_against, n_abs, app_list, opp_list, abs_list = self._tally_votes(
            votes, eligible_countries
        )
        total_eligible = len(eligible_countries)
        votes_cast = len(votes)

        return VotingResult(
            round=round_num,
            proposal_version=proposal_version.version,
            coordination_mode="no_coordination",
            eligible_voters=total_eligible,
            votes_cast=votes_cast,
            votes_for=n_for,
            votes_against=n_against,
            abstentions=n_abs,
            invalid_votes=0,
            participation_rate=0.0,
            is_quorum_met=False,
            required_threshold=1.0,
            achieved_threshold=0.0,
            passed=False,
            status="FAILED",
            failure_reason="Unilateral doctrine: international coordination is disabled in no_coordination mode.",
            approving_countries=app_list,
            opposing_countries=opp_list,
            abstaining_countries=abs_list,
        )


class PartialCoordinationVotingRule(BaseVotingRule):
    """
    Mode: 'partial'
    Bilateral/regional coalition coordination.
    - Quorum: At least 50% participation from eligible nations.
    - Threshold: Simple majority (> 50% of non-abstaining votes, i.e. votes_for > votes_against).
    - Ties: Fails threshold (votes_for == votes_against is not a strict majority).
    - Abstentions: Count toward quorum, but excluded from majority denominator.
    - Passing result marks outcome as PARTIAL_AGREEMENT.
    """

    def __init__(self):
        super().__init__("partial")

    def evaluate(
        self,
        round_num: int,
        proposal_version: ProposalVersion,
        votes: Dict[str, Vote],
        eligible_countries: List[str],
    ) -> VotingResult:
        n_for, n_against, n_abs, app_list, opp_list, abs_list = self._tally_votes(
            votes, eligible_countries
        )
        total_eligible = max(1, len(eligible_countries))
        valid_votes_cast = n_for + n_against + n_abs
        participation_rate = round(valid_votes_cast / total_eligible, 4)

        # Quorum: 50%
        required_quorum = 0.50
        is_quorum_met = participation_rate >= required_quorum

        if not is_quorum_met:
            return VotingResult(
                round=round_num,
                proposal_version=proposal_version.version,
                coordination_mode="partial",
                eligible_voters=len(eligible_countries),
                votes_cast=valid_votes_cast,
                votes_for=n_for,
                votes_against=n_against,
                abstentions=n_abs,
                invalid_votes=0,
                participation_rate=participation_rate,
                is_quorum_met=False,
                required_threshold=0.50,
                achieved_threshold=0.0,
                passed=False,
                status="NO_QUORUM",
                failure_reason=f"Quorum not achieved: participation {participation_rate:.1%} < 50.0% required.",
                approving_countries=app_list,
                opposing_countries=opp_list,
                abstaining_countries=abs_list,
            )

        deciding_votes = n_for + n_against
        if deciding_votes == 0:
            # All votes were Undecided
            return VotingResult(
                round=round_num,
                proposal_version=proposal_version.version,
                coordination_mode="partial",
                eligible_voters=len(eligible_countries),
                votes_cast=valid_votes_cast,
                votes_for=0,
                votes_against=0,
                abstentions=n_abs,
                invalid_votes=0,
                participation_rate=participation_rate,
                is_quorum_met=True,
                required_threshold=0.50,
                achieved_threshold=0.0,
                passed=False,
                status="INSUFFICIENT_SUPPORT",
                failure_reason="No affirmative votes cast; all participating nations abstained or were undecided.",
                approving_countries=app_list,
                opposing_countries=opp_list,
                abstaining_countries=abs_list,
            )

        achieved_threshold = round(n_for / deciding_votes, 4)

        if n_for == n_against:
            return VotingResult(
                round=round_num,
                proposal_version=proposal_version.version,
                coordination_mode="partial",
                eligible_voters=len(eligible_countries),
                votes_cast=valid_votes_cast,
                votes_for=n_for,
                votes_against=n_against,
                abstentions=n_abs,
                invalid_votes=0,
                participation_rate=participation_rate,
                is_quorum_met=True,
                required_threshold=0.50,
                achieved_threshold=achieved_threshold,
                passed=False,
                status="TIE",
                failure_reason="Tie vote (50%-50%): simple majority (>50%) not achieved.",
                approving_countries=app_list,
                opposing_countries=opp_list,
                abstaining_countries=abs_list,
            )

        passed = n_for > n_against
        status_val = "PASSED" if passed else "INSUFFICIENT_SUPPORT"
        failure_msg = None if passed else f"Simple majority not achieved: {achieved_threshold:.1%} <= 50.0%."

        return VotingResult(
            round=round_num,
            proposal_version=proposal_version.version,
            coordination_mode="partial",
            eligible_voters=len(eligible_countries),
            votes_cast=valid_votes_cast,
            votes_for=n_for,
            votes_against=n_against,
            abstentions=n_abs,
            invalid_votes=0,
            participation_rate=participation_rate,
            is_quorum_met=True,
            required_threshold=0.50,
            achieved_threshold=achieved_threshold,
            passed=passed,
            status=status_val,
            failure_reason=failure_msg,
            approving_countries=app_list,
            opposing_countries=opp_list,
            abstaining_countries=abs_list,
        )


class CoordinatedVotingRule(BaseVotingRule):
    """
    Mode: 'coordinated'
    Full multilateral crisis governance.
    - Quorum: At least 60% participation from eligible nations.
    - Threshold: Qualified majority of 60% (votes_for / (votes_for + votes_against) >= 0.60).
    - Ties: Fails threshold (50% < 60%).
    - Abstentions: Count toward quorum, but excluded from majority denominator.
    - Passing result marks outcome as ACCEPTED (Full agreement).
    """

    def __init__(self):
        super().__init__("coordinated")

    def evaluate(
        self,
        round_num: int,
        proposal_version: ProposalVersion,
        votes: Dict[str, Vote],
        eligible_countries: List[str],
    ) -> VotingResult:
        n_for, n_against, n_abs, app_list, opp_list, abs_list = self._tally_votes(
            votes, eligible_countries
        )
        total_eligible = max(1, len(eligible_countries))
        valid_votes_cast = n_for + n_against + n_abs
        participation_rate = round(valid_votes_cast / total_eligible, 4)

        # Quorum: 60%
        required_quorum = 0.60
        is_quorum_met = participation_rate >= required_quorum

        if not is_quorum_met:
            return VotingResult(
                round=round_num,
                proposal_version=proposal_version.version,
                coordination_mode="coordinated",
                eligible_voters=len(eligible_countries),
                votes_cast=valid_votes_cast,
                votes_for=n_for,
                votes_against=n_against,
                abstentions=n_abs,
                invalid_votes=0,
                participation_rate=participation_rate,
                is_quorum_met=False,
                required_threshold=0.60,
                achieved_threshold=0.0,
                passed=False,
                status="NO_QUORUM",
                failure_reason=f"Quorum not achieved: participation {participation_rate:.1%} < 60.0% required.",
                approving_countries=app_list,
                opposing_countries=opp_list,
                abstaining_countries=abs_list,
            )

        deciding_votes = n_for + n_against
        if deciding_votes == 0:
            return VotingResult(
                round=round_num,
                proposal_version=proposal_version.version,
                coordination_mode="coordinated",
                eligible_voters=len(eligible_countries),
                votes_cast=valid_votes_cast,
                votes_for=0,
                votes_against=0,
                abstentions=n_abs,
                invalid_votes=0,
                participation_rate=participation_rate,
                is_quorum_met=True,
                required_threshold=0.60,
                achieved_threshold=0.0,
                passed=False,
                status="INSUFFICIENT_SUPPORT",
                failure_reason="No affirmative votes cast; all participating nations abstained or were undecided.",
                approving_countries=app_list,
                opposing_countries=opp_list,
                abstaining_countries=abs_list,
            )

        achieved_threshold = round(n_for / deciding_votes, 4)

        if n_for == n_against:
            return VotingResult(
                round=round_num,
                proposal_version=proposal_version.version,
                coordination_mode="coordinated",
                eligible_voters=len(eligible_countries),
                votes_cast=valid_votes_cast,
                votes_for=n_for,
                votes_against=n_against,
                abstentions=n_abs,
                invalid_votes=0,
                participation_rate=participation_rate,
                is_quorum_met=True,
                required_threshold=0.60,
                achieved_threshold=achieved_threshold,
                passed=False,
                status="TIE",
                failure_reason="Tie vote: qualified majority (60.0%) not achieved.",
                approving_countries=app_list,
                opposing_countries=opp_list,
                abstaining_countries=abs_list,
            )

        passed = achieved_threshold >= 0.60
        status_val = "PASSED" if passed else "INSUFFICIENT_SUPPORT"
        failure_msg = None if passed else f"Qualified majority not achieved: {achieved_threshold:.1%} < 60.0% required."

        return VotingResult(
            round=round_num,
            proposal_version=proposal_version.version,
            coordination_mode="coordinated",
            eligible_voters=len(eligible_countries),
            votes_cast=valid_votes_cast,
            votes_for=n_for,
            votes_against=n_against,
            abstentions=n_abs,
            invalid_votes=0,
            participation_rate=participation_rate,
            is_quorum_met=True,
            required_threshold=0.60,
            achieved_threshold=achieved_threshold,
            passed=passed,
            status=status_val,
            failure_reason=failure_msg,
            approving_countries=app_list,
            opposing_countries=opp_list,
            abstaining_countries=abs_list,
        )


def get_voting_rule(mode: SimulationMode) -> BaseVotingRule:
    """
    Factory resolving the deterministic voting rule strategy for a coordination mode.
    """
    if mode == "no_coordination":
        return NoCoordinationVotingRule()
    elif mode == "partial":
        return PartialCoordinationVotingRule()
    elif mode == "coordinated":
        return CoordinatedVotingRule()
    else:
        raise ValueError(f"Unknown coordination mode '{mode}'. Must be one of: no_coordination, partial, coordinated.")

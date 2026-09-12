"""
Negotiation Service orchestrating the negotiation and voting subsystem (Phase 6).
Provides high-level methods to start sessions, execute rounds, and resolve outcomes.
"""
import logging
from typing import Dict, Optional

from app.negotiation.negotiation_session import NegotiationSessionManager
from app.schemas.coordinator_models import CoordinatorProposal
from app.schemas.data_models import CountryData
from app.schemas.negotiation_models import (
    NegotiationOutcome,
    NegotiationRound,
    NegotiationSession,
    Vote,
)
from app.schemas.simulation_models import SimulationState
from app.services.data_loader import default_data_loader

logger = logging.getLogger(__name__)


class NegotiationService:
    """
    Central orchestration service for negotiation sessions and voting rounds.
    """

    def __init__(self, countries_map: Optional[Dict[str, CountryData]] = None):
        self.countries_map = countries_map or {
            c.id: c for c in default_data_loader.load_all_countries()
        }

    def start_negotiation(
        self,
        state: SimulationState,
        proposal: Optional[CoordinatorProposal] = None,
        max_rounds: int = 3,
    ) -> NegotiationSession:
        """
        Creates and opens a new negotiation session.
        If proposal is not passed, selects the latest proposal from state.proposals.
        """
        if proposal is None:
            if not state.proposals:
                raise ValueError("Cannot start negotiation: simulation state has no coordinator proposals.")
            proposal = state.proposals[-1]

        session = NegotiationSessionManager.create_session(
            state=state,
            initial_proposal=proposal,
            max_rounds=max_rounds,
        )
        return session

    def execute_round(
        self,
        session: NegotiationSession,
        state: SimulationState,
        manual_votes: Optional[Dict[str, Vote]] = None,
    ) -> NegotiationRound:
        """
        Executes a single discrete negotiation round.
        """
        return NegotiationSessionManager.run_round(
            session=session,
            state=state,
            countries_map=self.countries_map,
            manual_votes=manual_votes,
        )

    def run_full_negotiation(
        self,
        session: NegotiationSession,
        state: SimulationState,
    ) -> NegotiationOutcome:
        """
        Executes rounds until a terminal state is reached (agreement, deadlock, or max rounds).
        """
        while session.outcome is None:
            self.execute_round(session=session, state=state)
            if session.outcome is not None:
                break
        return session.outcome


# Global default service singleton
default_negotiation_service = NegotiationService()

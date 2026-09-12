"""
Coordinator Service managing the lifecycle and invocation of the International Coordinator Agent.
"""
import asyncio
import concurrent.futures
from typing import Dict, Optional

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.coordinator_models import CoordinatorProposal
from app.llm import LLMProvider, get_llm_provider
from app.schemas.data_models import CountryData
from app.schemas.simulation_models import SimulationEvent, SimulationState
from app.services.data_loader import default_data_loader


class CoordinatorService:
    """
    Central service connecting the simulation engine and API layer to the
    International Coordinator Agent.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        coordinator_agent: Optional[CoordinatorAgent] = None,
        countries_map: Optional[Dict[str, CountryData]] = None,
    ):
        self.provider = provider or get_llm_provider()
        self.agent = coordinator_agent or CoordinatorAgent(provider=self.provider)
        self.countries_map = countries_map or {
            c.id: c for c in default_data_loader.load_all_countries()
        }

    async def request_coordination(
        self,
        state: SimulationState,
        current_event: Optional[SimulationEvent] = None,
        round_index: int = 1,
    ) -> CoordinatorProposal:
        """
        Asynchronously invokes the Coordinator Agent to synthesize positions
        and generate a validated proposal.
        """
        return await self.agent.propose(
            state=state,
            current_event=current_event,
            round_index=round_index,
            country_catalog=self.countries_map,
        )

    def request_coordination_sync(
        self,
        state: SimulationState,
        current_event: Optional[SimulationEvent] = None,
        round_index: int = 1,
    ) -> CoordinatorProposal:
        """
        Synchronous wrapper safe to call within synchronous simulation steps.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    asyncio.run,
                    self.request_coordination(state, current_event, round_index),
                )
                return future.result()
            return asyncio.run(self.request_coordination(state, current_event, round_index))
        else:
            return asyncio.run(self.request_coordination(state, current_event, round_index))


# Global default service singleton
default_coordinator_service = CoordinatorService()

"""
Country Decision Service managing agent instantiation, caching, and dispatch.
"""
import asyncio
from typing import Dict, Optional

from app.agents.country_agent import CountryAgent
from app.llm import LLMProvider, get_llm_provider
from app.schemas.data_models import CountryData, ScenarioData
from app.schemas.simulation_models import DecisionRecord, SimulationState
from app.services.data_loader import default_data_loader


class CountryDecisionService:
    """
    Central service connecting the simulation engine to Country Agents.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        countries_map: Optional[Dict[str, CountryData]] = None,
    ):
        self.provider = provider or get_llm_provider()
        self.countries_map = countries_map or {
            c.id: c for c in default_data_loader.load_all_countries()
        }
        self._agents: Dict[str, CountryAgent] = {}

    def get_agent(self, country_id: str) -> CountryAgent:
        """
        Retrieves or creates a reusable CountryAgent instance for a country.
        """
        if country_id not in self._agents:
            country = self.countries_map.get(country_id)
            if not country:
                country = default_data_loader.load_country(country_id)
            self._agents[country_id] = CountryAgent(
                country=country,
                provider=self.provider,
            )
        return self._agents[country_id]

    async def request_decision(
        self,
        country_id: str,
        state: SimulationState,
        scenario: ScenarioData,
        tick: int,
    ) -> DecisionRecord:
        """
        Asynchronously delegates a decision point to the country agent.
        """
        agent = self.get_agent(country_id)
        return await agent.decide(
            state=state,
            scenario=scenario,
            tick=tick,
        )

    def request_decision_sync(
        self,
        country_id: str,
        state: SimulationState,
        scenario: ScenarioData,
        tick: int,
    ) -> DecisionRecord:
        """
        Synchronous helper for executing decisions within synchronous engine ticks.
        Safe for execution whether or not an event loop is already running.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already in an event loop (e.g. inside FastAPI request),
            # run decision in executor to prevent nested event loop blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    asyncio.run,
                    self.request_decision(country_id, state, scenario, tick),
                )
                return future.result()
        else:
            return asyncio.run(self.request_decision(country_id, state, scenario, tick))


# Global default decision service
default_decision_service = CountryDecisionService()

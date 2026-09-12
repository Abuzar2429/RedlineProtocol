"""
Simulation Repository for managing active simulation sessions in memory.
"""
from typing import Dict, List, Optional

from app.schemas.simulation_models import SimulationState
from app.services.simulation.engine import SimulationEngine


class SimulationRepository:
    """
    In-memory thread-safe registry of simulation engines.
    """

    def __init__(self):
        self._simulations: Dict[str, SimulationEngine] = {}

    def save(self, engine: SimulationEngine) -> None:
        """
        Stores or updates an engine instance.
        """
        self._simulations[engine.simulation_id] = engine

    def get(self, simulation_id: str) -> Optional[SimulationEngine]:
        """
        Retrieves an active simulation engine by ID.
        """
        return self._simulations.get(simulation_id)

    def list_all(self) -> List[SimulationState]:
        """
        Lists state summaries for all registered simulations.
        """
        return [engine.state for engine in self._simulations.values()]

    def delete(self, simulation_id: str) -> bool:
        """
        Removes a simulation from memory.
        """
        if simulation_id in self._simulations:
            del self._simulations[simulation_id]
            return True
        return False

    def clear(self) -> None:
        """
        Clears all simulations (useful for testing).
        """
        self._simulations.clear()


# Global default repository
default_simulation_repository = SimulationRepository()

"""
Scoring Repository for managing evaluation records in memory.
"""
from typing import Dict, List, Optional

from app.schemas.scoring_models import ScoringResult


class ScoringRepository:
    """
    In-memory registry of calculated simulation scores.
    """

    def __init__(self):
        # Key: simulation_id -> ScoringResult
        self._scores: Dict[str, ScoringResult] = {}

    def save(self, score: ScoringResult) -> None:
        """
        Persists a scoring result.
        """
        self._scores[score.simulation_id] = score

    def get(self, simulation_id: str) -> Optional[ScoringResult]:
        """
        Retrieves the score for a specific simulation.
        """
        return self._scores.get(simulation_id)

    def list_all(self) -> List[ScoringResult]:
        """
        Lists all cached scoring results.
        """
        return list(self._scores.values())

    def delete(self, simulation_id: str) -> bool:
        """
        Removes a scoring record.
        """
        if simulation_id in self._scores:
            del self._scores[simulation_id]
            return True
        return False

    def clear(self) -> None:
        """
        Clears all scores (for testing).
        """
        self._scores.clear()


# Default singleton repository
default_scoring_repository = ScoringRepository()

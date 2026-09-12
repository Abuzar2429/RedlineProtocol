"""
Read-only crisis scenario data endpoints (Phase 2).
"""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.schemas.data_models import ScenarioData
from app.services.data_loader import default_data_loader

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=List[ScenarioData])
async def list_scenarios() -> List[ScenarioData]:
    """
    Returns the list of all available crisis scenarios for the simulator.
    """
    try:
        return default_data_loader.load_all_scenarios()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load crisis scenarios: {str(exc)}",
        )


@router.get("/{scenario_id}", response_model=ScenarioData)
async def get_scenario(scenario_id: str) -> ScenarioData:
    """
    Retrieves the structured specification for a specific crisis scenario by ID (e.g. 'scenario_01' or 'crisis_001').
    """
    try:
        return default_data_loader.load_scenario(scenario_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving scenario '{scenario_id}': {str(exc)}",
        )

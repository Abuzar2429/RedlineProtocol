"""
Read-only country data endpoints (Phase 2).
"""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.schemas.data_models import CountryData
from app.services.data_loader import default_data_loader

router = APIRouter(prefix="/api/countries", tags=["countries"])


@router.get("", response_model=List[CountryData])
async def list_countries() -> List[CountryData]:
    """
    Returns the list of all 15 fictional countries participating in the simulator.
    """
    try:
        return default_data_loader.load_all_countries()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load country profiles: {str(exc)}",
        )


@router.get("/{country_id}", response_model=CountryData)
async def get_country(country_id: str) -> CountryData:
    """
    Retrieves the detailed profile for a specific country by ID (e.g. 'country_01').
    """
    try:
        return default_data_loader.load_country(country_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID '{country_id}' not found",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving country '{country_id}': {str(exc)}",
        )

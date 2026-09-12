"""
Pydantic schemas for API responses and Data Layer models.
"""
from pydantic import BaseModel

from app.schemas.data_models import (
    CountryData,
    ScenarioData,
    TimelineEvent,
    ScenarioAction,
    GovernanceDocumentMetadata,
    GovernanceDocument,
)


class RootResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str


from app.schemas.simulation_models import (
    CountrySimulationStatus,
    CountrySimulationState,
    CrisisOperationalState,
    SimulationEventType,
    SimulationEvent,
    DecisionRecord,
    SimulationStatus,
    SimulationMode,
    SimulationState,
    CreateSimulationRequest,
    SimulationStepResponse,
)
from app.schemas.coordinator_models import (
    CoordinatorContext,
    CoordinatorProposal,
    CountryPositionSummary,
    DeterministicAggregation,
    PredictedVotes,
)

__all__ = [
    "RootResponse",
    "HealthResponse",
    "CountryData",
    "ScenarioData",
    "TimelineEvent",
    "ScenarioAction",
    "GovernanceDocumentMetadata",
    "GovernanceDocument",
    "CountrySimulationStatus",
    "CountrySimulationState",
    "CrisisOperationalState",
    "SimulationEventType",
    "SimulationEvent",
    "DecisionRecord",
    "SimulationStatus",
    "SimulationMode",
    "SimulationState",
    "CreateSimulationRequest",
    "SimulationStepResponse",
    "CoordinatorContext",
    "CoordinatorProposal",
    "CountryPositionSummary",
    "DeterministicAggregation",
    "PredictedVotes",
]

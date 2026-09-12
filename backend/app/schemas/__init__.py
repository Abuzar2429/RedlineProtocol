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
from app.schemas.negotiation_models import (
    NegotiationOutcome,
    NegotiationRound,
    NegotiationSession,
    NegotiationStatus,
    ProposalVersion,
    Vote,
    VoteType,
    VotingResult,
)

from app.schemas.scoring_models import (
    MetricId,
    ScoreGrade,
    MetricResult,
    SimulationMetrics,
    ScoringInputSnapshot,
    ScoringResult,
)
from app.schemas.websocket_models import (
    PublicCountryState,
    SimulationSnapshotPayload,
    WebSocketClientMessage,
    WebSocketEventEnvelope,
    WebSocketEventType,
)
from app.schemas.rag_models import (
    DocumentChunk,
    RetrievedEvidence,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGHealthResponse,
    RAGTrace,
    IngestionReport,
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
    "NegotiationOutcome",
    "NegotiationRound",
    "NegotiationSession",
    "NegotiationStatus",
    "ProposalVersion",
    "Vote",
    "VoteType",
    "VotingResult",
    "MetricId",
    "ScoreGrade",
    "MetricResult",
    "SimulationMetrics",
    "ScoringInputSnapshot",
    "ScoringResult",
    "PublicCountryState",
    "SimulationSnapshotPayload",
    "WebSocketClientMessage",
    "WebSocketEventEnvelope",
    "WebSocketEventType",
    "DocumentChunk",
    "RetrievedEvidence",
    "RAGQueryRequest",
    "RAGQueryResponse",
    "RAGHealthResponse",
    "RAGTrace",
    "IngestionReport",
]


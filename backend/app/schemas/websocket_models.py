"""
WebSocket schemas and event envelope models for Phase 8.

Defines the transport envelopes, client messages, and state snapshot representations:
- Adheres to spec §7.2 format: {type, time_offset, payload}
- Adheres to architecture event envelope: {event_id, event_type, type, simulation_id, tick, timestamp, payload}
- Enforces strict safety: zero exposure of private LLM reasoning, prompts, or credentials
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.simulation_models import (
    CountrySimulationStatus,
    SimulationMode,
    SimulationStatus,
)


WebSocketEventType = Literal[
    "event",
    "decision",
    "negotiation",
    "metrics",
    "complete",
    "state_snapshot",
    "error",
    "pong",
]


class PublicCountryState(BaseModel):
    """
    Sanitized public view of a country's simulation status.
    Excludes internal private reasoning, prompts, and inference metadata.
    """
    country_id: str = Field(..., description="Unique country identifier (e.g. 'country_01')")
    name: str = Field(..., description="Country display name")
    status: CountrySimulationStatus = Field(..., description="Public operational state: Unaware, Investigating, Notified, Coordinating")
    aware: bool = Field(..., description="Whether the country is publicly aware of the crisis")
    information_completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness of intelligence received")
    current_action: Optional[str] = Field(None, description="Most recently committed public action")
    coordination_status: Optional[str] = Field("Independent", description="Multilateral alignment")
    decision_count: int = Field(0, description="Total decisions committed")
    last_updated_tick: int = Field(0, description="Tick of last status change")


class SimulationSnapshotPayload(BaseModel):
    """
    Initial state payload sent immediately upon WebSocket connection
    to allow the client to populate all dashboard panels without full replay.
    """
    simulation_id: str = Field(..., description="Simulation identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    mode: SimulationMode = Field(..., description="Coordination architecture")
    status: SimulationStatus = Field(..., description="Current simulation execution status")
    current_tick: int = Field(..., ge=0, description="Current simulation tick (minutes)")
    current_time: str = Field(..., description="Virtual simulation clock formatted (e.g. 'T+14')")
    crisis_phase: str = Field(..., description="Current operational crisis phase")
    severity: str = Field(..., description="Crisis severity category")
    current_risk: float = Field(..., description="Current estimated operational risk (0-100)")
    countries: Dict[str, PublicCountryState] = Field(..., description="Map of sanitized country states")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Live dashboard metrics snapshot")
    recent_events: List[Dict[str, Any]] = Field(default_factory=list, description="Recent timeline events")
    active_proposal_id: Optional[str] = Field(None, description="ID of current active coordinator proposal if any")
    total_countries: int = Field(15, description="Total participating nations")
    connected_clients: int = Field(1, description="Number of active WebSocket clients on this simulation")


class WebSocketEventEnvelope(BaseModel):
    """
    Standard real-time event envelope streamed over WebSockets.
    Dual-compatible with spec §7.2 and the architectural audit envelope.
    """
    event_id: str = Field(default_factory=lambda: f"ws_{uuid.uuid4().hex[:10]}", description="Unique envelope event ID")
    type: WebSocketEventType = Field("event", description="High-level category matching spec §7.2 ('event', 'decision', 'negotiation', 'metrics', 'complete', 'state_snapshot')")
    event_type: str = Field(..., description="Fine-grained system event name (e.g. 'COUNTRY_DECISION', 'TICK_ADVANCED')")
    simulation_id: str = Field(..., description="Target simulation identifier")
    tick: int = Field(0, ge=0, description="Simulation virtual tick when event occurred")
    time_offset: int = Field(0, ge=0, description="Alias for tick matching spec §7.2")
    timestamp: str = Field("T+00", description="Virtual simulation timestamp formatted")
    wall_clock: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO UTC timestamp of transmission")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event data payload (sanitized of secrets and private reasoning)")


class WebSocketClientMessage(BaseModel):
    """
    Structured message sent from client to server over WebSocket.
    Allows interactive controls (stepping, pause, snapshot refresh, ping).
    """
    action: Literal["ping", "step", "get_snapshot", "start", "pause", "resume"] = Field(..., description="Requested control action")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional parameters for action")

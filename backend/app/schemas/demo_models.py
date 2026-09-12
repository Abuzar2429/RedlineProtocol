"""
Pydantic schemas and domain models for Phase 14: Demo Path, Seeded Replay & Fallbacks.

Defines:
- ExecutionMode ('LIVE' | 'DEMO' | 'REPLAY')
- DemoLaunchRequest and DemoRun models
- ReplaySession, ReplayEvent, and ReplayStateSnapshot models
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.comparison_models import ComparisonRun


ExecutionMode = Literal["LIVE", "DEMO", "REPLAY"]


class DemoLaunchRequest(BaseModel):
    """
    Request parameters for launching a presentation-ready deterministic demo.
    """
    scenario_id: str = Field("scenario_01", description="Crisis scenario identifier (default: 'scenario_01')")
    seed: int = Field(42, ge=0, le=999999, description="Deterministic seed for reproducible decisions and events")
    max_ticks: int = Field(60, ge=10, le=240, description="Virtual tick boundary per mode")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional presentation metadata")


class DemoRun(BaseModel):
    """
    Authoritative representation of a seeded demonstration session.
    Links directly to a Phase 13 Three-Mode Comparison run.
    """
    demo_id: str = Field(..., description="Unique demo session identifier (e.g. 'demo_seed42_...')")
    scenario_id: str = Field(..., description="Evaluated crisis scenario")
    scenario_title: str = Field(..., description="Fictional crisis headline")
    seed: int = Field(..., description="Deterministic seed used")
    execution_mode: Literal["DEMO"] = Field("DEMO", description="Execution mode: strictly DEMO")
    status: str = Field("COMPLETED", description="Lifecycle status: RUNNING | COMPLETED | FAILED")
    comparison_id: str = Field(..., description="Underlying Phase 13 Comparison identifier")
    comparison: Optional[ComparisonRun] = Field(None, description="Full three-mode comparison results")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp"
    )
    completed_at: Optional[str] = Field(None, description="ISO 8601 UTC completion timestamp")
    is_deterministic: bool = Field(True, description="Guaranteed deterministic and reproducible")
    fallback_active: bool = Field(False, description="Whether deterministic offline fallback was used")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReplayEvent(BaseModel):
    """
    Sanitized, ordered event record for deterministic replay.
    """
    sequence_number: int = Field(..., ge=0, description="Authoritative 0-indexed chronological ordering")
    tick: int = Field(..., ge=0, description="Virtual simulation tick")
    timestamp: str = Field("T+00", description="Formatted virtual simulation clock")
    event_type: str = Field(..., description="Event discriminator (e.g. 'CRISIS_TRIGGERED', 'COORDINATOR_PROPOSAL')")
    source: str = Field(..., description="Originating agent or system module")
    description: str = Field(..., description="Public event description")
    affected_countries: List[str] = Field(default_factory=list, description="Affected country IDs")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Sanitized event details")
    mode: Optional[str] = Field(None, description="Coordination mode context if from a comparison run")


class ReplaySession(BaseModel):
    """
    Recorded simulation or comparison session packaged for zero-recomputation playback.
    """
    replay_id: str = Field(..., description="Unique replay session identifier (e.g. 'replay_...')")
    source_type: Literal["simulation", "comparison"] = Field(..., description="Originating entity type")
    source_id: str = Field(..., description="Original simulation_id or comparison_id")
    scenario_id: str = Field(..., description="Crisis scenario identifier")
    scenario_title: str = Field(..., description="Human-readable crisis title")
    seed: Optional[int] = Field(None, description="Seeded configuration if originated from DEMO run")
    execution_mode: Literal["REPLAY"] = Field("REPLAY", description="Execution mode: strictly REPLAY")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_ticks: int = Field(..., ge=0, description="Authoritative virtual duration in ticks")
    total_events: int = Field(..., ge=0, description="Total chronological events in replay package")
    events: List[ReplayEvent] = Field(default_factory=list, description="Strictly ordered replay events")
    scoring_result: Optional[Dict[str, Any]] = Field(None, description="Authoritative recorded Phase 7 score")
    comparison_result: Optional[Dict[str, Any]] = Field(None, description="Authoritative recorded Phase 13 comparison")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReplayStateSnapshot(BaseModel):
    """
    Lightweight playback progress snapshot for frontend seek controls.
    """
    replay_id: str = Field(...)
    current_tick: int = Field(0, ge=0)
    current_time: str = Field("T+00")
    events_played: int = Field(0, ge=0)
    total_events: int = Field(0, ge=0)
    is_completed: bool = Field(False)
    visible_events: List[ReplayEvent] = Field(default_factory=list)

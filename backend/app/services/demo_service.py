"""
Demo and Replay Orchestration Service for Phase 14.

Manages:
1. Deterministic seeded demo execution across all three governance modes
2. Guaranteed offline, zero-dependency execution in DEMO mode
3. Packaging authoritative runs into ReplaySession models
4. Deterministic playback without re-running LLM, RAG, or scoring algorithms
5. Isolation: LIVE, DEMO, and REPLAY runs cannot mutate each other
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config.settings import settings
from app.schemas.comparison_models import CreateComparisonRequest
from app.schemas.demo_models import (
    DemoLaunchRequest,
    DemoRun,
    ReplayEvent,
    ReplaySession,
    ReplayStateSnapshot,
)
from app.scoring import default_scoring_repository
from app.services.comparison_service import (
    default_comparison_repository,
    default_comparison_service,
)
from app.services.data_loader import default_data_loader
from app.services.simulation.repository import default_simulation_repository
from app.services.websocket_manager import default_websocket_manager

logger = logging.getLogger(__name__)


class DemoRepository:
    """
    In-memory registry for DemoRun and ReplaySession instances.
    """

    def __init__(self):
        self._demos: Dict[str, DemoRun] = {}
        self._replays: Dict[str, ReplaySession] = {}

    def save_demo(self, demo: DemoRun) -> None:
        self._demos[demo.demo_id] = demo

    def get_demo(self, demo_id: str) -> Optional[DemoRun]:
        return self._demos.get(demo_id)

    def list_demos(self) -> List[DemoRun]:
        return list(self._demos.values())

    def save_replay(self, replay: ReplaySession) -> None:
        self._replays[replay.replay_id] = replay

    def get_replay(self, replay_id: str) -> Optional[ReplaySession]:
        return self._replays.get(replay_id)

    def list_replays(self) -> List[ReplaySession]:
        return list(self._replays.values())

    def clear(self) -> None:
        self._demos.clear()
        self._replays.clear()


default_demo_repository = DemoRepository()


class DemoService:
    """
    Orchestrates deterministic seeded presentations and replay generation.
    """

    def __init__(self, repository: Optional[DemoRepository] = None):
        self.repository = repository or default_demo_repository

    async def launch_demo(self, request: DemoLaunchRequest) -> DemoRun:
        """
        Launches a deterministic demo comparison for a fictional crisis scenario.
        Guaranteed to work without external LLM credentials or internet connectivity.
        """
        # Validate scenario exists
        scenario = default_data_loader.load_scenario(request.scenario_id)
        if not scenario:
            raise KeyError(f"Demo scenario '{request.scenario_id}' not found")

        demo_id = f"demo_seed{request.seed}_{uuid.uuid4().hex[:8]}"

        # Notify WebSocket
        await default_websocket_manager.broadcast_event(
            simulation_id=demo_id,
            event_type="DEMO_STARTED",
            payload={
                "demo_id": demo_id,
                "scenario_id": scenario.id,
                "seed": request.seed,
                "execution_mode": "DEMO",
            },
            category="event",
        )

        # 1. Initialize Phase 13 Three-Mode Comparison
        comp_req = CreateComparisonRequest(
            scenario_id=request.scenario_id,
            max_ticks=request.max_ticks,
            metadata={
                "demo_id": demo_id,
                "seed": request.seed,
                "execution_mode": "DEMO",
                "is_deterministic": True,
                "user_metadata": request.metadata,
            },
        )
        comp_run = default_comparison_service.create_comparison(comp_req)

        # 2. Execute three-mode comparison through existing engine
        completed_comp = await default_comparison_service.execute_comparison(comp_run.comparison_id)

        # 3. Assemble DemoRun
        now_utc = datetime.now(timezone.utc).isoformat()
        demo_run = DemoRun(
            demo_id=demo_id,
            scenario_id=scenario.id,
            scenario_title=scenario.title,
            seed=request.seed,
            execution_mode="DEMO",
            status="COMPLETED",
            comparison_id=completed_comp.comparison_id,
            comparison=completed_comp,
            created_at=now_utc,
            completed_at=now_utc,
            is_deterministic=True,
            fallback_active=True,
            metadata={
                "max_ticks": request.max_ticks,
                "winner": completed_comp.winner,
                "app_mode": settings.APP_MODE,
            },
        )
        self.repository.save_demo(demo_run)

        # 4. Automatically package into a ReplaySession for instant presentation replay
        self.create_replay_from_comparison(
            comparison_id=completed_comp.comparison_id,
            seed=request.seed,
            demo_id=demo_id,
        )

        # Broadcast completion
        await default_websocket_manager.broadcast_event(
            simulation_id=demo_id,
            event_type="DEMO_COMPLETED",
            payload={
                "demo_id": demo_id,
                "seed": request.seed,
                "winner": completed_comp.winner,
                "comparison_id": completed_comp.comparison_id,
            },
            category="complete",
        )

        return demo_run

    def restart_demo(self, demo_id: str, new_seed: Optional[int] = None) -> DemoLaunchRequest:
        """
        Prepares a fresh launch request for restarting a demo without reusing previous state.
        """
        existing = self.repository.get_demo(demo_id)
        if not existing:
            raise KeyError(f"Demo run '{demo_id}' not found")

        seed_to_use = new_seed if new_seed is not None else existing.seed
        return DemoLaunchRequest(
            scenario_id=existing.scenario_id,
            seed=seed_to_use,
            max_ticks=int(existing.metadata.get("max_ticks", 60)),
        )

    # ── Replay Generation ─────────────────────────────────────────────────────

    def create_replay_from_simulation(
        self, simulation_id: str, seed: Optional[int] = None
    ) -> ReplaySession:
        """
        Packages a recorded simulation into an immutable ReplaySession.
        Preserves original chronological event ordering and recorded scoring.
        """
        engine = default_simulation_repository.get(simulation_id)
        if not engine:
            raise KeyError(f"Simulation '{simulation_id}' not found for replay")

        replay_id = f"replay_{simulation_id[:12]}_{uuid.uuid4().hex[:6]}"

        # Build chronological ReplayEvents
        replay_events: List[ReplayEvent] = []
        for idx, ev in enumerate(engine.state.event_history):
            replay_events.append(
                ReplayEvent(
                    sequence_number=idx,
                    tick=ev.tick,
                    timestamp=f"T+{ev.tick:02d}",
                    event_type=ev.event_type,
                    source=ev.source,
                    description=ev.description,
                    affected_countries=ev.affected_countries,
                    payload=ev.payload,
                    mode=engine.state.mode,
                )
            )

        # Fetch recorded score if available
        scoring_res = default_scoring_repository.get(simulation_id)
        scoring_dict = scoring_res.model_dump() if scoring_res else None

        replay = ReplaySession(
            replay_id=replay_id,
            source_type="simulation",
            source_id=simulation_id,
            scenario_id=engine.state.scenario_id,
            scenario_title=engine.state.metadata.get("scenario_title", engine.state.scenario_id),
            seed=seed,
            execution_mode="REPLAY",
            total_ticks=engine.state.current_tick,
            total_events=len(replay_events),
            events=replay_events,
            scoring_result=scoring_dict,
            metadata={"mode": engine.state.mode},
        )
        self.repository.save_replay(replay)
        return replay

    def create_replay_from_comparison(
        self,
        comparison_id: str,
        seed: Optional[int] = None,
        demo_id: Optional[str] = None,
    ) -> ReplaySession:
        """
        Packages a recorded Three-Mode Comparison into an immutable ReplaySession.
        Aggregates events across all three modes in strictly preserved sequence.
        """
        comp = default_comparison_repository.get(comparison_id)
        if not comp:
            raise KeyError(f"Comparison '{comparison_id}' not found for replay")

        replay_id = f"replay_{comparison_id[:12]}_{uuid.uuid4().hex[:6]}"

        all_events: List[ReplayEvent] = []
        seq = 0

        # Collect events from each mode's simulation in authoritative order
        for mode in ("no_coordination", "partial", "coordinated"):
            res = comp.results.get(mode)
            if not res:
                continue
            engine = default_simulation_repository.get(res.simulation_id)
            if not engine:
                continue

            for ev in engine.state.event_history:
                all_events.append(
                    ReplayEvent(
                        sequence_number=seq,
                        tick=ev.tick,
                        timestamp=f"T+{ev.tick:02d}",
                        event_type=ev.event_type,
                        source=ev.source,
                        description=ev.description,
                        affected_countries=ev.affected_countries,
                        payload=ev.payload,
                        mode=mode,
                    )
                )
                seq += 1

        # Replay events are sorted strictly by tick then original sequence
        all_events.sort(key=lambda e: (e.tick, e.sequence_number))
        for idx, e in enumerate(all_events):
            e.sequence_number = idx

        max_tick = max((e.tick for e in all_events), default=0)

        replay = ReplaySession(
            replay_id=replay_id,
            source_type="comparison",
            source_id=comparison_id,
            scenario_id=comp.scenario_id,
            scenario_title=comp.scenario_title,
            seed=seed,
            execution_mode="REPLAY",
            total_ticks=max_tick,
            total_events=len(all_events),
            events=all_events,
            comparison_result=comp.model_dump(),
            metadata={
                "demo_id": demo_id,
                "winner": comp.winner,
                "modes": comp.modes_evaluated,
            },
        )
        self.repository.save_replay(replay)
        return replay

    def seek_replay(self, replay_id: str, to_tick: int) -> ReplayStateSnapshot:
        """
        Calculates a deterministic replay playback snapshot up to to_tick.
        Zero mutation to original recorded state.
        """
        replay = self.repository.get_replay(replay_id)
        if not replay:
            raise KeyError(f"ReplaySession '{replay_id}' not found")

        target_tick = max(0, min(to_tick, replay.total_ticks))
        visible = [e for e in replay.events if e.tick <= target_tick]

        return ReplayStateSnapshot(
            replay_id=replay_id,
            current_tick=target_tick,
            current_time=f"T+{target_tick:02d}",
            events_played=len(visible),
            total_events=replay.total_events,
            is_completed=(target_tick >= replay.total_ticks),
            visible_events=visible,
        )


default_demo_service = DemoService()

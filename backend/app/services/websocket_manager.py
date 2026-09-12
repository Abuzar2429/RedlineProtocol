"""
WebSocket Connection Manager and Real-Time Event Dispatcher for Phase 8.

Manages:
- Per-simulation isolated WebSocket connections
- Real-time event broadcasting to subscribed clients
- Automatic stale/disconnected client cleanup
- Non-blocking client delivery (<500ms target)
- Information boundary enforcement (sanitizes private reasoning & secrets)
- Initial state snapshot delivery upon connection
"""
import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.schemas.simulation_models import SimulationEvent, SimulationState
from app.schemas.websocket_models import (
    PublicCountryState,
    SimulationSnapshotPayload,
    WebSocketEventEnvelope,
    WebSocketEventType,
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages isolated WebSocket client connections per simulation.
    Guarantees strict isolation: events for Simulation A are never broadcast to Simulation B.
    """

    def __init__(self):
        # simulation_id -> set of active WebSocket instances
        self._active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, simulation_id: str, websocket: WebSocket) -> None:
        """
        Accepts and registers a new WebSocket connection for a specific simulation.
        """
        await websocket.accept()
        async with self._lock:
            self._active_connections[simulation_id].add(websocket)
            count = len(self._active_connections[simulation_id])

        logger.info(
            "WebSocket client connected to simulation [%s]. Active clients for simulation: %d",
            simulation_id,
            count,
        )

    async def disconnect(self, simulation_id: str, websocket: WebSocket) -> None:
        """
        Removes a WebSocket connection from the registry and cleans up empty entries.
        """
        async with self._lock:
            if simulation_id in self._active_connections:
                self._active_connections[simulation_id].discard(websocket)
                if not self._active_connections[simulation_id]:
                    del self._active_connections[simulation_id]

        logger.info(
            "WebSocket client disconnected from simulation [%s]. Remaining clients: %d",
            simulation_id,
            len(self._active_connections.get(simulation_id, set())),
        )

    def get_connection_count(self, simulation_id: str) -> int:
        """
        Returns number of active client connections for a simulation.
        """
        return len(self._active_connections.get(simulation_id, set()))

    def get_active_simulations(self) -> List[str]:
        """
        Lists all simulation IDs that currently have at least one active subscriber.
        """
        return list(self._active_connections.keys())

    # ── Broadcasting ───────────────────────────────────────────────────────────

    async def broadcast_to_simulation(self, simulation_id: str, message: Dict[str, Any]) -> int:
        """
        Broadcasts a serialized message payload to all clients connected to simulation_id.
        Catches dead/broken connections and cleans them up automatically.
        Returns the number of successfully notified clients.
        """
        # Fetch copy of current sockets without holding lock during network I/O
        async with self._lock:
            sockets = list(self._active_connections.get(simulation_id, set()))

        if not sockets:
            return 0

        dead_sockets: List[WebSocket] = []
        delivered = 0

        async def _send(ws: WebSocket):
            nonlocal delivered
            try:
                await ws.send_json(message)
                delivered += 1
            except (WebSocketDisconnect, RuntimeError, Exception) as exc:
                logger.debug(
                    "WebSocket delivery failed for client on simulation [%s]: %s",
                    simulation_id,
                    exc,
                )
                dead_sockets.append(ws)

        # Run concurrent delivery so slow clients don't block others
        await asyncio.gather(*[_send(ws) for ws in sockets], return_exceptions=True)

        # Remove dead sockets if any failed
        if dead_sockets:
            async with self._lock:
                for ws in dead_sockets:
                    if simulation_id in self._active_connections:
                        self._active_connections[simulation_id].discard(ws)
                if simulation_id in self._active_connections and not self._active_connections[simulation_id]:
                    del self._active_connections[simulation_id]

        return delivered

    async def broadcast_event(
        self,
        simulation_id: str,
        event_type: str,
        payload: Dict[str, Any],
        tick: int = 0,
        timestamp: str = "T+00",
        event_id: Optional[str] = None,
        category: Optional[WebSocketEventType] = None,
    ) -> Optional[WebSocketEventEnvelope]:
        """
        Constructs a sanitized WebSocketEventEnvelope and broadcasts it to simulation subscribers.
        """
        if self.get_connection_count(simulation_id) == 0:
            return None

        # Determine category matching spec §7.2 if not provided
        if not category:
            evt_upper = event_type.upper()
            if "DECISION" in evt_upper:
                cat: WebSocketEventType = "decision"
            elif "NEGOTIATION" in evt_upper or "VOTE" in evt_upper or "PROPOSAL" in evt_upper:
                cat = "negotiation"
            elif "METRICS" in evt_upper or "SCORE" in evt_upper:
                cat = "metrics"
            elif "COMPLETE" in evt_upper or "RESOLVED" in evt_upper:
                cat = "complete"
            else:
                cat = "event"
        else:
            cat = category

        # Sanitize payload: strip any private keys, internal prompts, or tracebacks
        sanitized_payload = self._sanitize_payload(payload)

        envelope = WebSocketEventEnvelope(
            event_id=event_id or f"ws_{uuid.uuid4().hex[:10]}",
            type=cat,
            event_type=event_type,
            simulation_id=simulation_id,
            tick=tick,
            time_offset=tick,
            timestamp=timestamp,
            payload=sanitized_payload,
        )

        await self.broadcast_to_simulation(simulation_id, envelope.model_dump())
        return envelope

    async def broadcast_simulation_event(
        self,
        simulation_id: str,
        event: SimulationEvent,
    ) -> Optional[WebSocketEventEnvelope]:
        """
        Convenience helper to broadcast an authoritative SimulationEvent from Phase 3.
        """
        return await self.broadcast_event(
            simulation_id=simulation_id,
            event_type=event.event_type,
            payload=event.payload,
            tick=event.tick,
            timestamp=f"T+{event.tick:02d}",
            event_id=event.event_id,
        )

    # ── Snapshot & State Serialization ────────────────────────────────────────

    def build_snapshot_payload(self, state: SimulationState) -> SimulationSnapshotPayload:
        """
        Extracts a clean, client-safe SimulationSnapshotPayload from authoritative SimulationState.
        """
        # Build sanitized public country states
        public_countries: Dict[str, PublicCountryState] = {}
        for cid, c_state in state.countries.items():
            public_countries[cid] = PublicCountryState(
                country_id=cid,
                name=c_state.name,
                status=c_state.status,
                aware=c_state.aware,
                information_completeness=round(c_state.information_completeness, 2),
                current_action=c_state.current_action,
                coordination_status=c_state.coordination_status or "Independent",
                decision_count=c_state.decision_count,
                last_updated_tick=c_state.last_updated_tick,
            )

        # Build live metrics snapshot
        metrics_data: Dict[str, Any] = {
            "current_risk": round(state.crisis_state.current_risk, 1),
            "coordination_ratio": 0.0,
            "countries_coordinating": sum(1 for c in state.countries.values() if c.status == "Coordinating"),
            "total_countries": len(state.countries),
        }

        # If proposals/negotiations exist, include coordination ratio
        if state.negotiations and state.negotiations[-1].outcome:
            outcome = state.negotiations[-1].outcome
            ratio = len(outcome.supporting_countries) / max(1, len(state.countries))
            metrics_data["coordination_ratio"] = round(ratio, 2)
            metrics_data["countries_coordinating"] = len(outcome.supporting_countries)
            metrics_data["agreement_reached"] = outcome.agreement_reached
            metrics_data["unresolved_issues_count"] = len(outcome.unresolved_issues)

        # Recent events (up to 15 latest)
        recent_events = [
            {
                "event_id": ev.event_id,
                "tick": ev.tick,
                "time_offset": ev.tick,
                "event_type": ev.event_type,
                "description": ev.description,
            }
            for ev in state.event_history[-15:]
        ]

        active_proposal = state.proposals[-1].proposal_id if state.proposals else None

        return SimulationSnapshotPayload(
            simulation_id=state.simulation_id,
            scenario_id=state.scenario_id,
            mode=state.mode,
            status=state.status,
            current_tick=state.current_tick,
            current_time=state.current_time,
            crisis_phase=state.crisis_state.phase,
            severity=state.crisis_state.severity,
            current_risk=round(state.crisis_state.current_risk, 1),
            countries=public_countries,
            metrics=metrics_data,
            recent_events=recent_events,
            active_proposal_id=active_proposal,
            total_countries=len(state.countries),
            connected_clients=max(1, self.get_connection_count(state.simulation_id)),
        )

    async def send_snapshot(self, simulation_id: str, websocket: WebSocket, state: SimulationState) -> None:
        """
        Sends an initial full state snapshot to a newly connected client.
        """
        snapshot = self.build_snapshot_payload(state)
        envelope = WebSocketEventEnvelope(
            event_id=f"snap_{uuid.uuid4().hex[:8]}",
            type="state_snapshot",
            event_type="INITIAL_STATE_SNAPSHOT",
            simulation_id=simulation_id,
            tick=state.current_tick,
            time_offset=state.current_tick,
            timestamp=state.current_time,
            payload=snapshot.model_dump(),
        )
        await websocket.send_json(envelope.model_dump())

    # ── Safety Sanitizer ──────────────────────────────────────────────────────

    def _sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters out any sensitive internal keys from payload dictionaries before broadcast.
        """
        forbidden_keys = {
            "api_key",
            "prompt",
            "system_prompt",
            "user_prompt",
            "hidden_reasoning",
            "chain_of_thought",
            "traceback",
            "sql",
            "password",
            "secret",
        }
        sanitized = {}
        for k, v in payload.items():
            if k.lower() in forbidden_keys:
                continue
            if isinstance(v, dict):
                sanitized[k] = self._sanitize_payload(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    self._sanitize_payload(item) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                sanitized[k] = v
        return sanitized


# Default singleton instance of the connection manager
default_websocket_manager = WebSocketConnectionManager()

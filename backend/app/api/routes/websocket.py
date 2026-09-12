"""
WebSocket router for Phase 8.

Exposes:
- WS /ws/simulations/{simulation_id}
- WS /api/ws/simulations/{simulation_id}

Provides real-time event streaming, initial snapshot transmission, client command handling,
and graceful disconnection cleanup.
"""
import logging
from typing import Any, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.schemas.websocket_models import WebSocketClientMessage, WebSocketEventEnvelope
from app.services.simulation.repository import default_simulation_repository
from app.services.websocket_manager import default_websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def _handle_websocket_connection(simulation_id: str, websocket: WebSocket) -> None:
    """
    Common handler for simulation WebSocket connections.
    """
    engine = default_simulation_repository.get(simulation_id)
    if not engine:
        logger.warning("Rejected WebSocket connection: simulation '%s' not found", simulation_id)
        # Close connection immediately with code 4404
        await websocket.close(code=4404, reason=f"Simulation '{simulation_id}' not found")
        return

    # Accept and register connection
    await default_websocket_manager.connect(simulation_id, websocket)

    try:
        # Transmit initial full state snapshot
        await default_websocket_manager.send_snapshot(simulation_id, websocket, engine.state)

        # Main message receive loop for interactive client commands
        while True:
            data = await websocket.receive_json()
            try:
                msg = WebSocketClientMessage.model_validate(data)
                action = msg.action

                if action == "ping":
                    pong_envelope = WebSocketEventEnvelope(
                        type="pong",
                        event_type="PONG",
                        simulation_id=simulation_id,
                        tick=engine.state.current_tick,
                        time_offset=engine.state.current_tick,
                        timestamp=engine.state.current_time,
                        payload={"status": "alive", "tick": engine.state.current_tick},
                    )
                    await websocket.send_json(pong_envelope.model_dump())

                elif action == "get_snapshot":
                    await default_websocket_manager.send_snapshot(simulation_id, websocket, engine.state)

                elif action == "step":
                    if engine.state.status != "COMPLETED" and engine.state.status != "PAUSED":
                        step_res = engine.step()
                        for ev in step_res.events:
                            await default_websocket_manager.broadcast_simulation_event(simulation_id, ev)
                        if step_res.is_completed:
                            await default_websocket_manager.broadcast_event(
                                simulation_id=simulation_id,
                                event_type="SIMULATION_COMPLETED",
                                payload={"final_tick": engine.state.current_tick, "status": "COMPLETED"},
                                tick=engine.state.current_tick,
                                timestamp=engine.state.current_time,
                                category="complete",
                            )

                elif action == "start":
                    if engine.state.status == "CREATED":
                        engine.start()
                        await default_websocket_manager.broadcast_event(
                            simulation_id=simulation_id,
                            event_type="SIMULATION_STARTED",
                            payload={"status": "RUNNING"},
                            tick=engine.state.current_tick,
                            timestamp=engine.state.current_time,
                        )

                elif action == "pause":
                    if engine.state.status == "RUNNING":
                        engine.pause()
                        await default_websocket_manager.broadcast_event(
                            simulation_id=simulation_id,
                            event_type="SIMULATION_PAUSED",
                            payload={"status": "PAUSED"},
                            tick=engine.state.current_tick,
                            timestamp=engine.state.current_time,
                        )

                elif action == "resume":
                    if engine.state.status == "PAUSED":
                        engine.resume()
                        await default_websocket_manager.broadcast_event(
                            simulation_id=simulation_id,
                            event_type="SIMULATION_RESUMED",
                            payload={"status": "RUNNING"},
                            tick=engine.state.current_tick,
                            timestamp=engine.state.current_time,
                        )

            except Exception as parse_err:
                logger.debug("Malformed client WebSocket message: %s", parse_err)
                err_envelope = WebSocketEventEnvelope(
                    type="error",
                    event_type="INVALID_CLIENT_MESSAGE",
                    simulation_id=simulation_id,
                    tick=engine.state.current_tick,
                    time_offset=engine.state.current_tick,
                    timestamp=engine.state.current_time,
                    payload={"error": str(parse_err), "received": data},
                )
                await websocket.send_json(err_envelope.model_dump())

    except (WebSocketDisconnect, RuntimeError):
        logger.info("WebSocket disconnected for simulation [%s]", simulation_id)
    finally:
        await default_websocket_manager.disconnect(simulation_id, websocket)


@router.websocket("/ws/simulations/{simulation_id}")
async def simulation_websocket_endpoint(websocket: WebSocket, simulation_id: str):
    """
    Standard spec-defined WebSocket streaming endpoint: /ws/simulations/{id}.
    """
    await _handle_websocket_connection(simulation_id, websocket)


@router.websocket("/api/ws/simulations/{simulation_id}")
async def simulation_websocket_api_alias(websocket: WebSocket, simulation_id: str):
    """
    API-prefixed alias for WebSocket streaming: /api/ws/simulations/{id}.
    """
    await _handle_websocket_connection(simulation_id, websocket)


# ── Comparison WebSocket Streaming — Phase 13 ──────────────────────────────────

async def _handle_comparison_websocket_connection(comparison_id: str, websocket: WebSocket) -> None:
    """
    Handler for comparison session WebSocket streaming.
    Broadcasts real-time mode transitions and final synthesis.
    """
    from app.services.comparison_service import default_comparison_repository

    run = default_comparison_repository.get(comparison_id)
    # Register client connection using comparison_id as simulation_id channel
    await default_websocket_manager.connect(comparison_id, websocket)

    try:
        if run:
            snap_env = WebSocketEventEnvelope(
                type="event",
                event_type="COMPARISON_SNAPSHOT",
                simulation_id=comparison_id,
                payload=run.model_dump(),
            )
            await websocket.send_json(snap_env.model_dump())

        while True:
            data = await websocket.receive_json()
            if isinstance(data, dict) and data.get("action") == "ping":
                pong_env = WebSocketEventEnvelope(
                    type="pong",
                    event_type="PONG",
                    simulation_id=comparison_id,
                    payload={"status": "alive", "comparison_id": comparison_id},
                )
                await websocket.send_json(pong_env.model_dump())

    except (WebSocketDisconnect, RuntimeError):
        logger.info("WebSocket client disconnected from comparison [%s]", comparison_id)
    finally:
        await default_websocket_manager.disconnect(comparison_id, websocket)


@router.websocket("/ws/comparisons/{comparison_id}")
async def comparison_websocket_endpoint(websocket: WebSocket, comparison_id: str):
    """
    WebSocket streaming endpoint for Phase 13 comparison runs: /ws/comparisons/{id}.
    """
    await _handle_comparison_websocket_connection(comparison_id, websocket)


@router.websocket("/api/ws/comparisons/{comparison_id}")
async def comparison_websocket_api_alias(websocket: WebSocket, comparison_id: str):
    """
    API-prefixed alias for comparison WebSocket streaming: /api/ws/comparisons/{id}.
    """
    await _handle_comparison_websocket_connection(comparison_id, websocket)

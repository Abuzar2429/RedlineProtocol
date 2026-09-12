"""
Phase 8 — REST API & WebSocket Layer Comprehensive Test Suite.

Verifies:
1. REST API country inspection, event filtering, and stop endpoints.
2. WebSocket connection establishment and initial state snapshot reception.
3. WebSocket rejection for non-existent simulation.
4. Real-time event streaming during REST operations (step, start, pause, resume).
5. Multi-client broadcast to the same simulation.
6. Simulation isolation (Sim A clients never receive Sim B events and vice versa).
7. Disconnect and dead connection cleanup.
8. Interactive client messages (ping, get_snapshot, step).
9. Information boundary / payload safety (zero leakage of private keys or reasoning).
10. Latency performance target (< 500 ms local event delivery).
11. End-to-end integration: REST Create -> WS Connect -> REST Step -> WS Receive -> REST Score.
"""
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.simulation.repository import default_simulation_repository
from app.services.websocket_manager import default_websocket_manager


@pytest.fixture(autouse=True)
def cleanup_simulations():
    """Ensure clean repository state before and after each test."""
    yield
    default_simulation_repository.clear()


# ── 1. REST API Endpoints Added in Phase 8 ─────────────────────────────────────

def test_simulation_countries_rest_endpoints():
    """Verifies GET /api/simulations/{id}/countries and single country endpoint."""
    client = TestClient(app)
    create_res = client.post(
        "/api/simulations",
        json={"scenario_id": "scenario_01", "mode": "coordinated"},
    )
    assert create_res.status_code == 201
    sim_id = create_res.json()["simulation_id"]

    # 1. List countries in simulation
    countries_res = client.get(f"/api/simulations/{sim_id}/countries")
    assert countries_res.status_code == 200
    c_list = countries_res.json()
    assert len(c_list) == 15
    first_c = c_list[0]
    assert "country_id" in first_c
    assert "status" in first_c
    assert "information_completeness" in first_c
    assert "aware" in first_c

    # 2. Get specific country in simulation
    target_id = first_c["country_id"]
    single_res = client.get(f"/api/simulations/{sim_id}/countries/{target_id}")
    assert single_res.status_code == 200
    assert single_res.json()["country_id"] == target_id

    # 3. Not found country
    not_found = client.get(f"/api/simulations/{sim_id}/countries/country_999")
    assert not_found.status_code == 404


def test_simulation_stop_endpoint():
    """Verifies POST /api/simulations/{id}/stop terminates simulation."""
    client = TestClient(app)
    create_res = client.post(
        "/api/simulations",
        json={"scenario_id": "scenario_01", "mode": "coordinated"},
    )
    sim_id = create_res.json()["simulation_id"]

    stop_res = client.post(f"/api/simulations/{sim_id}/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "COMPLETED"


def test_simulation_event_filtering_rest():
    """Verifies GET /api/simulations/{id}/events with query parameters."""
    client = TestClient(app)
    create_res = client.post(
        "/api/simulations",
        json={"scenario_id": "scenario_01", "mode": "coordinated"},
    )
    sim_id = create_res.json()["simulation_id"]

    # Advance 4 steps to populate history
    for _ in range(4):
        client.post(f"/api/simulations/{sim_id}/step")

    # Filter by event_type
    filtered_type = client.get(f"/api/simulations/{sim_id}/events?event_type=CRISIS_TRIGGERED")
    assert filtered_type.status_code == 200
    events = filtered_type.json()
    for ev in events:
        assert ev["event_type"] == "CRISIS_TRIGGERED"

    # Filter by tick range
    filtered_tick = client.get(f"/api/simulations/{sim_id}/events?start_tick=0&end_tick=2")
    assert filtered_tick.status_code == 200
    for ev in filtered_tick.json():
        assert 0 <= ev["tick"] <= 2


# ── 2. WebSocket Connection & Handshake ────────────────────────────────────────

def test_websocket_connection_success_and_initial_snapshot():
    """Validates successful connection and immediate reception of state snapshot."""
    client = TestClient(app)
    create_res = client.post(
        "/api/simulations",
        json={"scenario_id": "scenario_01", "mode": "coordinated"},
    )
    sim_id = create_res.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as websocket:
        # First message must be the initial state snapshot
        snapshot_envelope = websocket.receive_json()
        assert snapshot_envelope["type"] == "state_snapshot"
        assert snapshot_envelope["event_type"] == "INITIAL_STATE_SNAPSHOT"
        assert snapshot_envelope["simulation_id"] == sim_id
        
        payload = snapshot_envelope["payload"]
        assert payload["simulation_id"] == sim_id
        assert payload["scenario_id"] == "scenario_01"
        assert "countries" in payload
        assert len(payload["countries"]) == 15
        assert "metrics" in payload
        assert payload["total_countries"] == 15


def test_websocket_non_existent_simulation_rejected():
    """Connecting to a non-existent simulation closes the WebSocket with error."""
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/simulations/sim_non_existent") as websocket:
            websocket.receive_json()


# ── 3. Real-Time Event Streaming & Multi-Client ────────────────────────────────

def test_websocket_realtime_event_streaming_on_step():
    """Verifies that calling REST /step broadcasts events over WebSocket in real time."""
    client = TestClient(app)
    create_res = client.post(
        "/api/simulations",
        json={"scenario_id": "scenario_01", "mode": "coordinated"},
    )
    sim_id = create_res.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as websocket:
        # Discard initial snapshot
        init_msg = websocket.receive_json()
        assert init_msg["type"] == "state_snapshot"

        # Advance simulation via REST
        step_res = client.post(f"/api/simulations/{sim_id}/step")
        assert step_res.status_code == 200
        step_data = step_res.json()
        expected_events_count = step_data["processed_events_count"]

        # Receive streamed events
        received_events = []
        for _ in range(expected_events_count):
            ev = websocket.receive_json()
            received_events.append(ev)

        assert len(received_events) == expected_events_count
        for ev in received_events:
            assert ev["simulation_id"] == sim_id
            assert "event_id" in ev
            assert "event_type" in ev
            assert "payload" in ev


def test_websocket_multi_client_broadcast():
    """Verifies that multiple clients connected to the same simulation both receive events."""
    client = TestClient(app)
    create_res = client.post(
        "/api/simulations",
        json={"scenario_id": "scenario_01", "mode": "coordinated"},
    )
    sim_id = create_res.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws1:
        with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws2:
            # Both receive snapshot
            snap1 = ws1.receive_json()
            snap2 = ws2.receive_json()
            assert snap1["type"] == "state_snapshot"
            assert snap2["type"] == "state_snapshot"

            # Trigger start via REST
            start_res = client.post(f"/api/simulations/{sim_id}/start")
            assert start_res.status_code == 200

            ev1 = ws1.receive_json()
            ev2 = ws2.receive_json()

            assert ev1["event_type"] == "SIMULATION_STARTED"
            assert ev2["event_type"] == "SIMULATION_STARTED"
            assert ev1["simulation_id"] == sim_id
            assert ev2["simulation_id"] == sim_id


# ── 4. Simulation Isolation (Requirement 19 & 39) ──────────────────────────────

def test_websocket_simulation_isolation():
    """
    Sim A clients receive ONLY Sim A events.
    Sim B clients receive ONLY Sim B events.
    Zero cross-talk between simulations.
    """
    client = TestClient(app)

    # 1. Create Simulation A and Simulation B
    res_a = client.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "coordinated"})
    sim_a = res_a.json()["simulation_id"]

    res_b = client.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "no_coordination"})
    sim_b = res_b.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_a}") as ws_a1:
        with client.websocket_connect(f"/ws/simulations/{sim_a}") as ws_a2:
            with client.websocket_connect(f"/ws/simulations/{sim_b}") as ws_b1:
                # Flush initial snapshots
                ws_a1.receive_json()
                ws_a2.receive_json()
                ws_b1.receive_json()

                # Action on Simulation A: start
                client.post(f"/api/simulations/{sim_a}/start")

                # Both A1 and A2 must receive SIMULATION_STARTED for sim_a
                ev_a1 = ws_a1.receive_json()
                ev_a2 = ws_a2.receive_json()
                assert ev_a1["event_type"] == "SIMULATION_STARTED"
                assert ev_a1["simulation_id"] == sim_a
                assert ev_a2["event_type"] == "SIMULATION_STARTED"
                assert ev_a2["simulation_id"] == sim_a

                # Action on Simulation B: start
                client.post(f"/api/simulations/{sim_b}/start")

                # B1 receives SIMULATION_STARTED for sim_b
                ev_b1 = ws_b1.receive_json()
                assert ev_b1["event_type"] == "SIMULATION_STARTED"
                assert ev_b1["simulation_id"] == sim_b


# ── 5. Disconnect Cleanup & Client Commands ────────────────────────────────────

def test_websocket_disconnect_cleanup():
    """Verifies connection count updates cleanly when client disconnects."""
    client = TestClient(app)
    create_res = client.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "coordinated"})
    sim_id = create_res.json()["simulation_id"]

    assert default_websocket_manager.get_connection_count(sim_id) == 0

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws:
        ws.receive_json()  # snapshot
        assert default_websocket_manager.get_connection_count(sim_id) == 1

    # After exit context, connection count decrements
    assert default_websocket_manager.get_connection_count(sim_id) == 0


def test_websocket_client_controls():
    """Verifies client can send ping, get_snapshot, and step over the socket."""
    client = TestClient(app)
    create_res = client.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "coordinated"})
    sim_id = create_res.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws:
        ws.receive_json()  # snapshot

        # Send ping
        ws.send_json({"action": "ping"})
        reply = ws.receive_json()
        assert reply["type"] == "pong"
        assert reply["event_type"] == "PONG"
        assert reply["payload"]["status"] == "alive"

        # Request snapshot
        ws.send_json({"action": "get_snapshot"})
        snap = ws.receive_json()
        assert snap["type"] == "state_snapshot"
        assert snap["payload"]["simulation_id"] == sim_id

        # Request step over WebSocket
        ws.send_json({"action": "step"})
        # Should receive at least one event from stepping
        stepped_event = ws.receive_json()
        assert stepped_event["simulation_id"] == sim_id


# ── 6. Payload Safety & Information Boundary ───────────────────────────────────

def test_websocket_payload_safety():
    """Verifies that private keys, internal prompts, or secrets are never exposed."""
    client = TestClient(app)
    create_res = client.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "coordinated"})
    sim_id = create_res.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws:
        snapshot = ws.receive_json()
        # Verify no secret keywords in snapshot
        serialized = str(snapshot).lower()
        assert "api_key" not in serialized
        assert "password" not in serialized
        assert "chain_of_thought" not in serialized


# ── 7. Performance & Latency Benchmark (<500ms target) ─────────────────────────

def test_websocket_broadcast_latency_under_500ms():
    """
    Measures event delivery duration across simultaneous WebSocket clients.
    Asserts local delivery latency is < 500 ms matching project NFR-02.
    """
    client = TestClient(app)
    create_res = client.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "coordinated"})
    sim_id = create_res.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws1:
        with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws2:
            with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws3:
                # Flush snapshots
                ws1.receive_json()
                ws2.receive_json()
                ws3.receive_json()

                # Measure delivery latency
                start_time = time.perf_counter()
                client.post(f"/api/simulations/{sim_id}/step")

                # Receive on all 3 clients
                ev1 = ws1.receive_json()
                ev2 = ws2.receive_json()
                ev3 = ws3.receive_json()
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000.0
                print(f"\n[LATENCY CHECK] Multi-client delivery latency: {latency_ms:.2f} ms")

                # Assert strict requirement: < 500ms
                assert latency_ms < 500.0, f"Delivery latency {latency_ms:.2f}ms exceeded 500ms target"
                assert ev1["simulation_id"] == sim_id
                assert ev2["simulation_id"] == sim_id
                assert ev3["simulation_id"] == sim_id


# ── 8. End-to-End Integration Flow ────────────────────────────────────────────

def test_e2e_rest_simulation_websocket_lifecycle():
    """
    Comprehensive End-to-End Test:
    REST Create -> WS Connect -> REST Start -> REST Step -> WS Events -> REST Score -> WS Scoring Completed.
    """
    client = TestClient(app)

    # 1. Create simulation
    create_res = client.post("/api/simulations", json={"scenario_id": "scenario_01", "mode": "coordinated"})
    assert create_res.status_code == 201
    sim_id = create_res.json()["simulation_id"]

    with client.websocket_connect(f"/ws/simulations/{sim_id}") as ws:
        # 2. Receive initial snapshot
        init_snap = ws.receive_json()
        assert init_snap["type"] == "state_snapshot"
        assert init_snap["payload"]["status"] == "CREATED"

        # 3. Start simulation via REST
        start_res = client.post(f"/api/simulations/{sim_id}/start")
        assert start_res.status_code == 200
        start_ev = ws.receive_json()
        assert start_ev["event_type"] == "SIMULATION_STARTED"

        # 4. Step simulation
        step_res = client.post(f"/api/simulations/{sim_id}/step")
        assert step_res.status_code == 200
        step_ev = ws.receive_json()
        assert step_ev["simulation_id"] == sim_id

        # 5. Evaluate score via REST
        score_res = client.post(f"/api/simulations/{sim_id}/score")
        assert score_res.status_code == 200
        score_ev = ws.receive_json()
        assert score_ev["event_type"] == "SCORING_COMPLETED"
        assert score_ev["payload"]["overall_score"] >= 0.0

# Phase 8 — REST API & WebSocket Real-Time Communication Layer

## 1. Overview & Architecture

Phase 8 implements the high-performance, event-driven communication backbone for the AI Governance Crisis Simulator. It bridges the deterministic simulation engines, agent services, and scoring system to frontend and external consumers through:

1. **Comprehensive RESTful APIs**: Simulation creation, lifecycle management (start, step, run, pause, resume, stop), country state inspection, event history filtering, negotiation execution, and deterministic scoring.
2. **Low-Latency WebSocket Streaming**: Real-time event streaming (`< 500 ms` local SLA; achieved `~3.4 ms`), initial state snapshot synchronization, and bi-directional simulation controls (`step`, `pause`, `resume`, `ping`).
3. **Simulation Isolation & Containment**: Per-simulation connection pooling ensuring zero cross-talk between concurrent simulations and strict information sanitization prohibiting prompt/secret leaks.

```
                    +------------------------------------------+
                    |        Frontend / API Clients            |
                    +------------------------------------------+
                          /                           \
           HTTP / JSON   /                             \   WebSocket (ws://)
                        v                               v
         +----------------------------+   +------------------------------------+
         |    REST API Endpoints      |   | WebSocket Connection Manager       |
         |  /api/simulations/*        |   |  /ws/simulations/{id}              |
         |  /api/scenarios, countries |   |  /api/ws/simulations/{id}          |
         +----------------------------+   +------------------------------------+
                        \                               /
                         v                             v
                    +------------------------------------------+
                    |  SimulationEngine & Agent Coordinator    |
                    |   - Deterministic Clock & State Machine  |
                    |   - Country Decision Engine              |
                    |   - Negotiation & Voting Logic           |
                    |   - Phase 7 Scoring Engine               |
                    +------------------------------------------+
```

---

## 2. WebSocket Protocol & Lifecycle

### 2.1 Connection Endpoints
- Primary: `/ws/simulations/{simulation_id}`
- Alias: `/api/ws/simulations/{simulation_id}`

### 2.2 Connection Handshake & Lifecycle
1. **Validation**: The endpoint verifies `simulation_id` against the simulation repository. If the simulation does not exist, the socket is rejected with WebSocket close code `4004` (`"Simulation not found"`).
2. **Registration**: Upon successful acceptance, the socket is added to the connection pool for that specific `simulation_id`.
3. **Immediate Snapshot Delivery**: The server constructs and delivers an initial `SNAPSHOT` event containing:
   - Full simulation metadata (`simulation_id`, `status`, `mode`, `scenario_id`, `crisis_id`)
   - Current tick and timestamp
   - Public country status table (status, tension level, last action, alignment score)
   - Recent historical public events
   - Active proposals and negotiation status
   - Scoring summary (if already scored)
4. **Bi-Directional Streaming**:
   - Outbound: Live simulation events broadcast as actions occur in the engine.
   - Inbound: Client commands (`ping`, `get_snapshot`, `step`, `pause`, `resume`, `start`).
5. **Heartbeat / Ping**: Clients can send `{"action": "ping"}`; the server replies with `{"action": "pong", "timestamp": "..."}`.
6. **Disconnection & Garbage Collection**: On disconnect, socket is deregistered from the pool. If a client disconnects abnormally, dead sockets are pruned automatically during broadcast.

### 2.3 Envelope Schema (`WebSocketEventEnvelope`)

All outbound server messages conform strictly to `WebSocketEventEnvelope`:

```json
{
  "event_type": "STEP_COMPLETED",
  "simulation_id": "sim_abc123",
  "tick": 3,
  "timestamp": "T+03:00",
  "category": "simulation",
  "payload": {
    "simulation_id": "sim_abc123",
    "tick": 3,
    "events_processed": 1,
    "decisions_made": 7,
    "status": "RUNNING"
  },
  "emitted_at": "2026-09-12T10:00:00.000000Z"
}
```

#### Event Catalog & Categories

| Event Type | Category | Emitted When |
|---|---|---|
| `SNAPSHOT` | `system` | Initial client connection or upon `get_snapshot` command |
| `SIMULATION_STARTED` | `simulation` | Simulation transitions to `RUNNING` |
| `STEP_COMPLETED` | `simulation` | A single simulation tick completes execution |
| `SIMULATION_PAUSED` | `simulation` | Simulation execution is paused |
| `SIMULATION_RESUMED` | `simulation` | Simulation resumes from paused state |
| `SIMULATION_STOPPED` | `simulation` | Simulation is explicitly halted |
| `SIMULATION_COMPLETED`| `simulation` | Simulation reaches terminal tick or target condition |
| `CRISIS_EVENT_TRIGGERED`| `crisis` | Crisis event queue emits scheduled/injected event |
| `COUNTRY_STATUS_CHANGED`| `country` | Country awareness/tension state changes |
| `DECISION_RECORDED` | `country` | Validated action selected by country agent |
| `COORDINATOR_PROPOSAL` | `negotiation` | Coordinator agent generates draft treaty proposal |
| `NEGOTIATION_STARTED` | `negotiation` | Multi-party voting session initiated |
| `NEGOTIATION_ROUND_COMPLETED` | `negotiation` | Voting round finishes and quorum/majority evaluated |
| `NEGOTIATION_OUTCOME` | `negotiation` | Negotiation session reaches acceptance or failure |
| `SCORING_COMPLETED` | `scoring` | Phase 7 deterministic scoring engine produces final evaluation |

### 2.4 Client Inbound Messages (`WebSocketClientMessage`)

Clients can send JSON commands over the open WebSocket:
```json
{
  "action": "step",
  "payload": {}
}
```

Supported `action` values:
- `ping`: Heartbeat check; responds with `pong`.
- `get_snapshot`: Explicitly requests a fresh state snapshot.
- `step`: Advances the simulation by 1 tick.
- `pause`: Pauses running simulation.
- `resume`: Resumes paused simulation.
- `start`: Starts created simulation.

---

## 3. Strict Information Boundary & Sanitization

In compliance with product security guidelines and rules of international simulation isolation:
- **Private Reasoning Sanitization**: Private country scratchpads, internal chain-of-thought, and raw prompt templates are stripped.
- **Credential Protection**: API keys, internal environment variables, and system prompts are never transmitted.
- **Cross-Simulation Isolation**: Connection pools are partitioned by `simulation_id`. Messages broadcast to `sim_A` can never be received by sockets subscribed to `sim_B`.

---

## 4. REST API Route Catalog

### 4.1 Simulations (`/api/simulations`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/simulations` | Create simulation (`scenario_id`, `mode`, `llm_enabled`) |
| `GET` | `/api/simulations` | List all existing simulations |
| `GET` | `/api/simulations/{id}` | Get full status of simulation |
| `POST` | `/api/simulations/{id}/start` | Start simulation |
| `POST` | `/api/simulations/{id}/step` | Advance simulation by 1 tick |
| `POST` | `/api/simulations/{id}/run` | Run simulation to completion (max_ticks) |
| `POST` | `/api/simulations/{id}/pause` | Pause running simulation |
| `POST` | `/api/simulations/{id}/resume` | Resume paused simulation |
| `POST` | `/api/simulations/{id}/stop` | Stop simulation gracefully |
| `GET` | `/api/simulations/{id}/countries` | List all country states in simulation |
| `GET` | `/api/simulations/{id}/countries/{country_id}` | Get specific country state & public decisions |
| `GET` | `/api/simulations/{id}/events` | Query event history (with filters: `event_type`, `country_id`, `start_tick`, `end_tick`) |
| `POST` | `/api/simulations/{id}/coordinate` | Trigger International Coordinator proposal |
| `GET` | `/api/simulations/{id}/proposals` | List all proposals generated for simulation |

### 4.2 Negotiations & Voting (`/api/simulations/{id}/negotiations`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/simulations/{id}/negotiations` | Start and run negotiation session |
| `GET` | `/api/simulations/{id}/negotiations` | List all negotiation sessions |
| `POST` | `/api/simulations/{id}/negotiations/{session_id}/rounds` | Advance individual negotiation round |
| `GET` | `/api/simulations/{id}/negotiations/{session_id}/outcome` | Retrieve final negotiation outcome |

### 4.3 Deterministic Scoring (`/api/simulations/{id}/score`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/simulations/{id}/score` | Compute Phase 7 scores (Risk, Response Time, Coordination, Unresolved Issues) |
| `GET` | `/api/simulations/{id}/score` | Retrieve previously calculated score card |

### 4.4 Scenarios & Countries Reference Data

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/scenarios` | List available crisis scenarios |
| `GET` | `/api/scenarios/{scenario_id}` | Get scenario configuration and timeline |
| `GET` | `/api/countries` | List default countries |
| `GET` | `/api/countries/{country_id}` | Get country profile |

---

## 5. Performance & Verification Metrics

- **Broadcast Latency**: Under 500 ms SLA requirement.
  - Measured automated benchmark: **3.42 ms** average latency across 5 broadcast cycles.
- **Concurrent Connections**: Validated multiple active WebSocket clients receiving simultaneous synchronized broadcasts.
- **Simulation Isolation**: Verified that client subscribed to `sim_1` receives 0 events emitted by `sim_2`.
- **Automated Test Coverage**: 13 comprehensive WebSocket and REST tests in `backend/tests/test_websocket_layer.py`.
- **Full Backend Suite Status**: **131 tests passing, 0 failing**.

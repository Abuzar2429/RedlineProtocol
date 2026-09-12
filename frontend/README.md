# AI Governance Crisis Simulator — Frontend

React 19 + TypeScript + Vite + Zustand + Tailwind CSS frontend shell for the AI Governance Crisis Simulator.

---

## 1. Overview & Architecture

The frontend serves as the operator command center shell for the AI Governance Crisis Simulator:
- **Authoritative Backend**: Simulation engine, deterministic scoring, country agent decisions, and RAG knowledge remain strictly backend responsibilities.
- **Frontend Role**: Visualizes simulation telemetry, dispatches operator commands (`step`, `run`, `pause`, `resume`, `stop`), and consumes live event streams over WebSockets.
- **Multi-Simulation Isolation**: State management enforces strict isolation; events for simulation $A$ are rejected if the active store is tracking simulation $B$.

```
React UI (AppShell)
   ↓
Pages (DashboardPage, SimulationPage, NotFoundPage)
   ↓
Zustand Stores (simulationStore, connectionStore, uiStore)
   ↓
Communication Layer (ApiClient + SimulationWebSocketClient)
   ↓
FastAPI Backend (REST API + WebSocket /ws/simulations/{id})
```

---

## 2. Directory Structure

```
frontend/src/
├── app/
│   └── router.tsx               # React Router route tree
├── components/
│   ├── feedback/                # ConnectionStatusIndicator, ToastContainer, Loading, Error, Empty states
│   └── layout/                  # AppShell, Header, Sidebar
├── pages/
│   ├── Dashboard/               # Scenario selector, mode picker, launcher, RAG health
│   ├── Simulation/              # Active simulation shell with controls and Phase 11-13 foundation slots
│   └── NotFound/                # 404 fallback
├── services/
│   ├── api/                     # Typed REST ApiClient
│   └── websocket/               # Resilient SimulationWebSocketClient & Event Dispatcher
├── stores/
│   ├── connectionStore.ts       # WebSocket state, reconnect attempts, timestamps
│   ├── simulationStore.ts       # Authoritative simulation telemetry & snapshot
│   └── uiStore.ts               # Sidebar collapse and toast notifications
├── types/                       # Shared contracts matching backend schemas
└── test/                        # Vitest unit & integration test suites
```

---

## 3. Environment Variables

Create `.env` or `.env.local` if custom backend hosts are required:

```env
# Optional overrides (defaults to Vite proxy /api and /ws)
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## 4. Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server on port `5173` |
| `npm run build` | Typecheck (`tsc -b`) and build production bundle |
| `npm test` | Run Vitest unit and integration test suite |
| `npm run lint` | Run Oxlint fast linter |
| `npm run preview` | Preview production build |

---

## 5. WebSocket Event Lifecycle & Reconnection

- **Endpoint**: `ws://localhost:8000/ws/simulations/{simulation_id}`
- **Heartbeat**: Periodic ping frames dispatched every 25 seconds.
- **Reconnection**: Automatic exponential backoff up to 5 bounded attempts (1s, 2s, 4s, 8s, 10s max delay) on unexpected disconnection.
- **Intentional Teardown**: Cleanly disconnects and halts timers on unmount or session switch.

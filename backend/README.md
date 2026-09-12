# AI Governance Crisis Simulator — Backend

FastAPI + PostgreSQL backend for the AI Governance Crisis Simulator.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv

# Activate — Windows PowerShell
.venv\Scripts\Activate.ps1
# Activate — Unix/macOS
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Start the development server
uvicorn app.main:app --reload
```

## Simulation Engine (Phase 3)

The simulator uses a virtual event clock (`T+00`, `T+01`, ...) and a deterministic state machine to drive crises without requiring real-world time or external services.

> **Note on AI Agents**: LLM agents are intentionally not part of Phase 3. The simulation core operates completely deterministically using rule-based placeholder decisions mapped to national strategic profiles. This proves the complete simulation lifecycle and state machine in a reproducible, testable environment before adding LLM agents in Phase 4.

### Core Lifecycle:
```text
Scenario Data
     ↓
Create Simulation (T+00)
     ↓
Information Asymmetry (gated by delay)
     ↓
Sequential Country State Progression:
Unaware ──► Investigating ──► Notified ──► Coordinating
     ↓
Decision Point (Deterministic Policy Response)
     ↓
Action Execution & Operational Risk Deduction
     ↓
Resolution Accord / Simulation Complete
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | API root |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI (dev) |
| GET | `/api/countries` | List all 15 fictional countries |
| GET | `/api/countries/{id}` | Get country profile |
| GET | `/api/scenarios` | List all 3 crisis scenarios |
| GET | `/api/scenarios/{id}` | Get scenario definition |
| POST | `/api/simulations` | Create a new simulation session |
| GET | `/api/simulations` | List active simulations |
| GET | `/api/simulations/{id}` | Get simulation state |
| POST | `/api/simulations/{id}/start` | Start simulation |
| POST | `/api/simulations/{id}/step` | Execute a single virtual tick |
| POST | `/api/simulations/{id}/run` | Run simulation until completion |
| POST | `/api/simulations/{id}/pause` | Pause running simulation |
| POST | `/api/simulations/{id}/resume` | Resume paused simulation |
| GET | `/api/simulations/{id}/events` | Chronological event history |

## Running Tests and Data Validation

```bash
# Run full pytest suite (Phases 1, 2, 3)
pytest tests/ -v

# Run data consistency checker
python validate_data.py
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory and routes
│   ├── config/              # Settings (env vars)
│   ├── core/                # Database engine & session
│   ├── api/routes/          # REST route handlers (countries, scenarios, simulations)
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas (data models, simulation models)
│   └── services/
│       ├── data_loader.py   # Phase 2 dataset loader
│       └── simulation/      # Phase 3 deterministic engine
│           ├── clock.py          # Virtual deterministic tick clock
│           ├── event_queue.py    # Priority event queue
│           ├── decision_maker.py # Zero-LLM deterministic decisions
│           ├── event_processor.py# State transition handlers
│           ├── engine.py         # Main lifecycle coordinator
│           └── repository.py     # In-memory session store
├── data/                    # Phase 2 static datasets
│   ├── countries/           # 15 fictional country JSON profiles
│   ├── scenarios/           # 3 crisis scenario YAML definitions
│   └── governance/          # 6 governance knowledge documents
├── tests/                   # Pytest suites
└── validate_data.py         # Data validation CLI
```

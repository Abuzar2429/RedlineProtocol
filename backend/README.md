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

## Country Agents (Phase 4)

Phase 4 introduces AI-powered decision-making for the 15 fictional countries while preserving the deterministic simulation engine.

```text
                    Scenario
                       ↓
                Simulation Engine
                       ↓
                Decision Required
                       ↓
              ┌──────────────────┐
              │  Country Agent   │
              │      (LLM)       │
              └────────┬─────────┘
                       ↓
                 Structured
                   Decision
                       ↓
              Pydantic Validation
                       ↓
              Simulation Engine
                       ↓
                  State Update
```

- **Reusable Agent Architecture**: A single `CountryAgent` class parameterized by national profiles (`strategic_priorities`, `risk_tolerance`, `ai_policy_position`, etc.).
- **Strict Information Boundary**: Agents receive only verified public information and their own local awareness state. Hidden future events or private deliberations of rival states are strictly filtered out.
- **Provider Abstraction**: Supports `MockLLMProvider` (default, zero-cost, zero-key testing) and `AnthropicProvider` (live Claude model).
- **Deterministic Fallback**: If an LLM call fails, times out, or produces invalid schema, the engine activates a deterministic fallback (`source = "deterministic_fallback"`), ensuring simulations never crash or stall.

### LLM Configuration (.env)

```bash
# Provider choices: "mock" (default, zero-cost, no key needed) | "anthropic" | "openai"
LLM_PROVIDER=mock
LLM_MODEL=claude-sonnet-4-6
LLM_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
LLM_TEMPERATURE=0.7
LLM_TIMEOUT=30.0
LLM_MAX_RETRIES=1
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

---

## Phase 5 — International Coordinator Agent

### Architecture & Role
Country agents produce sovereign national positions; the **International Coordinator Agent** synthesizes those positions into a balanced proposed international response.
- **Dedicated Mandate**: Acts as the neutral coordination secretariat. Does not impersonate any country or favor allied blocs.
- **No Self-Approval**: Proposals are returned with status `PROPOSED`. The Coordinator **cannot** mark proposals as `APPROVED` or mutate simulation state. Negotiation rounds and voting are cleanly deferred to **Phase 6**.
- **Provider Reuse**: Reuses the unified `LLMProvider` abstraction (`MockLLMProvider` and `AnthropicProvider`).
- **Prompt Injection Boundary**: Treats country outputs and crisis reports as untrusted data.

### Strict Information Boundary
The Coordinator context builder strictly prevents intelligence leakage:
- **No Private Country Reasoning**: Internal classified reasoning and LLM chains-of-thought are strictly excluded; only shareable decision data (`action_id`, `willingness_to_coordinate`, public risk notes) is provided.
- **No Future Events**: Only events up to `current_tick` are visible.
- **Code-Calculated Aggregation**: Stance and vote counts are computed deterministically in Python before invoking the LLM.

### Proposal Schema (`CoordinatorProposal`)
Key fields:
- `proposal_id`: Unique traceable ID (e.g. `prop_001_sim_99eb_t06`)
- `simulation_id`, `event_id`, `tick`, `round`
- `proposal_type`: `JOINT_RESPONSE | INFORMATION_SHARING | TECHNICAL_ASSISTANCE | INVESTIGATION_COMMISSION`
- `title` & `summary`
- `items`: List of actionable multilateral items
- `rationale`: Balancing sovereignty and systemic safety
- `predicted_votes`: Dict with `approve`, `oppose`, `abstain` (validated against known country IDs)
- `unresolved_issues`: Contested points blocking full consensus
- `supporting_countries` & `opposing_countries`
- `confidence`: Bounded between 0.0 and 1.0
- `source`: `"llm_coordinator"` or `"deterministic_fallback"`
- `status`: Always `"PROPOSED"`

### Deterministic Fallback
If the LLM provider fails, times out, or returns invalid schema data, the Coordinator triggers code-driven deterministic fallback synthesis:
- Analyzes aware nations and majority action.
- Derives minimal common-ground response items.
- Sets `source = "deterministic_fallback"`.
- 100% reproducible and deterministic across identical state inputs.

### Configuration
```env
COORDINATOR_MODEL=claude-sonnet-4-6
COORDINATOR_TEMPERATURE=0.3
```

### Endpoints
- `POST /api/simulations/{id}/coordinate` — Trigger coordination proposal generation
- `GET /api/simulations/{id}/proposals` — List all proposals produced for a simulation
- `GET /api/simulations/{id}/proposals/{proposal_id}` — Retrieve a specific proposal


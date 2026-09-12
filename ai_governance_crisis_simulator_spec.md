# AI Governance Crisis Simulator
## Technical Specification & Implementation Roadmap

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Data Layer Specification](#3-data-layer-specification)
4. [Core Modules](#4-core-modules)
5. [AI Agent Design](#5-ai-agent-design)
6. [Scoring & Metrics Engine](#6-scoring--metrics-engine)
7. [API Specification](#7-api-specification)
8. [Frontend Specification](#8-frontend-specification)
9. [Tech Stack](#9-tech-stack)
10. [Implementation Roadmap](#10-implementation-roadmap)
11. [Folder Structure](#11-folder-structure)
12. [Future Enhancements](#12-future-enhancements)

---

## 1. Project Overview

### What It Is

An AI-powered multi-agent simulation platform that models how nations and international organizations respond to AI governance crises. The system is **not a chatbot** — it is a structured scenario engine where existing LLMs act as reasoning backends, and the platform supplies crisis data, country profiles, governance rules, event timelines, and deterministic scoring.

### Core Thesis

> The same crisis, governed differently, produces measurably different outcomes.

The simulator demonstrates this by running identical crises under different coordination strategies and quantifying the results.

### What Makes It Novel

- Information asymmetry between countries (not all parties know the same thing at the same time)
- Multi-agent negotiation with conflicting national priorities
- Deterministic outcome scoring (not LLM-hallucinated metrics)
- Comparative simulation: run the same crisis 3 ways, show the delta

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                    │
│         (Dashboard / Live Feed / Metrics)           │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                     │
│                                                     │
│  ┌─────────────────┐   ┌────────────────────────┐  │
│  │ Simulation      │   │ RAG Engine              │  │
│  │ Engine          │   │                         │  │
│  │ - Event clock   │   │ - Document retriever    │  │
│  │ - State machine │   │ - Vector DB (Chroma)    │  │
│  │ - Action engine │   │ - Governance docs index │  │
│  └────────┬────────┘   └───────────┬─────────────┘  │
│           │                        │                │
│  ┌────────▼────────────────────────▼─────────────┐  │
│  │              Agent Orchestrator                │  │
│  │                                               │  │
│  │   Country Agent × N    International Agent   │  │
│  │   (LLM-backed, per     (Coordinator /        │  │
│  │    country profile)     Negotiator)           │  │
│  └────────────────────────┬───────────────────────┘  │
│                           │                          │
│  ┌────────────────────────▼───────────────────────┐  │
│  │             Metrics Engine (Deterministic)     │  │
│  │   - Risk score   - Response time               │  │
│  │   - Coordination - Unresolved issues           │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼───────────────────┐
        ▼                  ▼                   ▼
   PostgreSQL          ChromaDB           Anthropic API
   (state, logs)    (vector store)       (claude-sonnet-4-6)
```

### Communication Protocol

- REST API for scenario setup, start/stop, config
- WebSocket for live event streaming to frontend
- Server-Sent Events (SSE) as fallback for real-time updates

---

## 3. Data Layer Specification

### 3.1 Country Profile Schema

```json
{
  "country_id": "string (ISO 3166-1 alpha-2)",
  "name": "string",
  "flag_emoji": "string",
  "priorities": ["national_security", "economic_stability", "privacy", "human_rights", "AI_development", "regulation"],
  "risk_tolerance": "low | medium | high",
  "transparency": "low | medium | high",
  "coordination_willingness": "low | medium | high",
  "decision_speed": "slow | medium | fast",
  "ai_capability_level": "low | medium | high",
  "international_influence": 0.0,
  "geopolitical_bloc": "string | null"
}
```

**Example — Security-Focused Nation:**
```json
{
  "country_id": "US",
  "name": "Country Alpha",
  "flag_emoji": "🇦🇺",
  "priorities": ["national_security", "economic_stability", "international_cooperation"],
  "risk_tolerance": "medium",
  "transparency": "medium",
  "coordination_willingness": "high",
  "decision_speed": "fast",
  "ai_capability_level": "high",
  "international_influence": 0.9,
  "geopolitical_bloc": "bloc_a"
}
```

**Example — Privacy-First Nation:**
```json
{
  "country_id": "DE",
  "name": "Country Beta",
  "flag_emoji": "🇧🇪",
  "priorities": ["privacy", "human_rights", "regulation"],
  "risk_tolerance": "low",
  "transparency": "high",
  "coordination_willingness": "high",
  "decision_speed": "medium",
  "ai_capability_level": "medium",
  "international_influence": 0.6,
  "geopolitical_bloc": "bloc_b"
}
```

---

### 3.2 Crisis Scenario Schema

```yaml
scenario_id: string
title: string
description: string
severity: low | medium | high | critical
severity_score: float (0.0 – 1.0)

affected_countries: list[country_id]
origin_country: country_id

information_delay:
  country_id: minutes_offset (int)

timeline:
  - time_offset: int (minutes)
    event: string
    type: detection | spread | escalation | media | diplomatic | resolution

initial_evidence_completeness: float (0.0 – 1.0)
evidence_grows_at: float (rate per minute)

potential_impacts:
  - infrastructure
  - financial_markets
  - public_services
  - national_security
  - public_trust

available_actions:
  - id: string
    label: string
    risk_reduction_value: float
    coordination_effect: float
    requires_agreement: bool
    visibility: public | private | bilateral

governance_docs_relevant:
  - doc_id: string
```

**Example Scenario:**
```yaml
scenario_id: "crisis_001"
title: "Cross-Border AI Infrastructure Failure"
description: "A highly capable autonomous AI system causes cascading failures across shared digital infrastructure, affecting financial clearing, energy grid coordination, and communications in 15 nations."
severity: "critical"
severity_score: 0.91

affected_countries: ["US", "DE", "IN", "BR", "JP", "CA", "AU", "FR", "GB", "KR", "SG", "ZA", "MX", "NG", "ID"]
origin_country: "US"

information_delay:
  US: 0
  CA: 3
  GB: 5
  DE: 5
  FR: 6
  JP: 8
  AU: 8
  KR: 9
  IN: 10
  BR: 12
  SG: 12
  MX: 13
  ZA: 15
  NG: 18
  ID: 20

initial_evidence_completeness: 0.4
evidence_grows_at: 0.03
```

---

### 3.3 Governance Document Index

```
/data/governance/
  ai_principles.pdf           # OECD AI Principles
  incident_response.pdf       # AI Incident Response Framework
  international_cooperation.pdf
  data_sharing_protocols.pdf
  emergency_procedures.pdf
  liability_frameworks.pdf
  national_ai_strategies/
    strategy_us.pdf
    strategy_eu.pdf
    strategy_in.pdf
```

Each document is chunked, embedded, and stored in ChromaDB. Metadata per chunk:

```json
{
  "doc_id": "string",
  "title": "string",
  "category": "principles | response | cooperation | liability | strategy",
  "relevance_tags": ["string"],
  "chunk_index": "int"
}
```

---

### 3.4 Simulation State Schema (PostgreSQL)

```sql
-- Simulation sessions
CREATE TABLE simulations (
  id UUID PRIMARY KEY,
  scenario_id TEXT,
  mode TEXT,               -- 'no_coordination' | 'partial' | 'coordinated'
  status TEXT,             -- 'running' | 'complete' | 'paused'
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  final_metrics JSONB
);

-- Per-country state
CREATE TABLE country_states (
  simulation_id UUID REFERENCES simulations(id),
  country_id TEXT,
  aware BOOLEAN DEFAULT FALSE,
  information_completeness FLOAT DEFAULT 0.0,
  current_action TEXT,
  coordination_status TEXT,
  last_updated TIMESTAMP,
  PRIMARY KEY (simulation_id, country_id)
);

-- Event log
CREATE TABLE events (
  id SERIAL PRIMARY KEY,
  simulation_id UUID REFERENCES simulations(id),
  time_offset INT,
  event_type TEXT,
  country_id TEXT,
  description TEXT,
  payload JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Agent decisions
CREATE TABLE decisions (
  id SERIAL PRIMARY KEY,
  simulation_id UUID REFERENCES simulations(id),
  country_id TEXT,
  time_offset INT,
  action_id TEXT,
  reasoning TEXT,
  risks_noted TEXT,
  expected_reactions TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Negotiation rounds
CREATE TABLE negotiations (
  id SERIAL PRIMARY KEY,
  simulation_id UUID REFERENCES simulations(id),
  round INT,
  proposals JSONB,
  votes JSONB,
  outcome TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. Core Modules

### 4.1 Simulation Engine

Manages the event clock and state machine.

```python
class SimulationEngine:
    def __init__(self, scenario: Scenario, countries: list[Country], mode: str):
        self.scenario = scenario
        self.countries = countries
        self.mode = mode
        self.clock = 0  # minutes
        self.state = SimulationState()
        self.metrics = MetricsEngine()

    def tick(self):
        """Advance simulation by 1 minute."""
        self.clock += 1
        self._process_information_spread()
        self._trigger_timeline_events()
        self._update_evidence_completeness()
        self._check_negotiation_triggers()

    def _process_information_spread(self):
        for country in self.countries:
            delay = self.scenario.information_delay[country.id]
            if self.clock >= delay:
                country.state.aware = True
                country.state.information_completeness = min(
                    1.0,
                    self.scenario.initial_evidence_completeness
                    + (self.clock - delay) * self.scenario.evidence_grows_at
                )

    def run(self) -> SimulationResult:
        while not self._is_resolved():
            self.tick()
            yield self.state  # stream to frontend
        return self.metrics.compute_final()
```

---

### 4.2 Event Engine

```python
TIMELINE_EVENTS = [
    {"offset": 0,  "type": "detection",   "description": "Origin country AI monitoring detects anomaly"},
    {"offset": 3,  "type": "verification","description": "Internal team verifies anomaly is real"},
    {"offset": 5,  "type": "spread",      "description": "Adjacent countries receive partial data"},
    {"offset": 8,  "type": "media",       "description": "Social media reports surface publicly"},
    {"offset": 11, "type": "diplomatic",  "description": "Formal notification to international body"},
    {"offset": 14, "type": "escalation",  "description": "International alert issued"},
    {"offset": 18, "type": "negotiation", "description": "Emergency meeting convened"},
    {"offset": 25, "type": "resolution",  "description": "Countries negotiate joint response"},
    {"offset": 32, "type": "agreement",   "description": "Joint action voted on"},
]
```

---

### 4.3 RAG Engine

```python
class RAGEngine:
    def __init__(self, chroma_client, embedding_model):
        self.db = chroma_client
        self.embedder = embedding_model

    def retrieve(self, query: str, top_k: int = 5) -> list[Document]:
        embedding = self.embedder.encode(query)
        results = self.db.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas"]
        )
        return results

    def build_context(self, country: Country, crisis: Crisis) -> str:
        query = f"{crisis.title} {' '.join(country.priorities)} governance response"
        docs = self.retrieve(query)
        return "\n\n".join([d["text"] for d in docs])
```

---

## 5. AI Agent Design

### 5.1 Country Agent

Each country agent receives a structured prompt assembled from:
- Country profile
- Current crisis state
- Available evidence
- Governance document context (via RAG)
- Other countries' known positions
- Available actions

**System Prompt Template:**
```
You are the AI Policy Advisor for {country_name}.

## National Priorities
{priorities_list}

## Risk Tolerance
{risk_tolerance}

## Current Crisis
{crisis_title}: {crisis_description}

## Your Information State
- Awareness: {aware}
- Evidence completeness: {evidence_pct}%
- Time since detection: {time_offset} minutes

## Other Countries' Known Positions
{other_positions}

## Relevant Governance Frameworks
{rag_context}

## Available Actions
{actions_list}

Respond with:
1. Recommended action (choose one from the list)
2. Reasoning (2-3 sentences)
3. Key risks (bullet list)
4. Expected reaction from other nations

Respond in JSON format only.
```

**Response Schema:**
```json
{
  "action_id": "string",
  "reasoning": "string",
  "risks": ["string"],
  "expected_reactions": "string",
  "willingness_to_coordinate": 0.0
}
```

---

### 5.2 International Coordinator Agent

The coordinator synthesizes positions and proposes agreements.

**Prompt Template:**
```
You are the coordinator of an international AI governance body.

## Crisis
{crisis_summary}

## Country Positions
{all_country_positions}

## Agreements Attempted So Far
{past_proposals}

Propose a joint action that maximizes country agreement.
Structure the proposal as specific, actionable items.
Identify which countries are likely to approve, oppose, or abstain.

Respond in JSON format only.
```

**Response Schema:**
```json
{
  "proposal": {
    "items": ["string"],
    "rationale": "string"
  },
  "predicted_votes": {
    "approve": ["country_id"],
    "oppose": ["country_id"],
    "abstain": ["country_id"]
  },
  "unresolved_issues": ["string"]
}
```

---

### 5.3 Agent Orchestration Flow

```
Simulation Clock Tick
        │
        ▼
Information Spread Engine
        │
        ▼
  For each aware country:
        │
        ▼
   Assemble prompt
   (profile + state + RAG)
        │
        ▼
   LLM call → Decision
        │
        ▼
   Apply action to state
   (update risk score, coordination status)
        │
        ▼
  Negotiation trigger?
  (enough countries aware + action requires agreement)
        │
      Yes
        ▼
  Coordinator agent builds proposal
        │
        ▼
  Countries vote (deterministic based on priorities + proposal content)
        │
        ▼
  Record outcome
        │
        ▼
  Metrics engine computes scores
```

**Optimization:** Only run LLM calls for countries that have new information or are in a negotiation round. Lightweight countries (low influence, fast decision speed) can use rule-based decisions to save API calls.

---

## 6. Scoring & Metrics Engine

All metrics are **deterministic** — computed by the simulation, not generated by the LLM.

### 6.1 Risk Score

```python
INITIAL_RISK = 100.0

ACTION_RISK_REDUCTIONS = {
    "investigate_internally":        -5,
    "notify_international":         -15,
    "suspend_system_temporarily":   -30,
    "share_technical_evidence":     -10,
    "request_joint_investigation":  -15,
    "issue_public_warning":          -5,
    "impose_temporary_restrictions": -12,
    "bilateral_information_share":   -8,
}

def compute_risk(actions_taken: list[str], coordination_ratio: float) -> float:
    risk = INITIAL_RISK
    for action in actions_taken:
        risk += ACTION_RISK_REDUCTIONS.get(action, 0)
    # Coordination multiplier: higher coordination = better risk reduction
    risk *= (1 - 0.2 * coordination_ratio)
    return max(0.0, risk)
```

### 6.2 Response Time

```python
def compute_response_time(detection_time: int, coordinated_action_time: int) -> int:
    return coordinated_action_time - detection_time  # in minutes
```

### 6.3 Coordination Score

```python
def compute_coordination(approving: int, total: int) -> float:
    return approving / total  # 0.0 – 1.0
```

### 6.4 Unresolved Issues

Extracted deterministically from the coordinator agent's `unresolved_issues` field, filtered by:
- Issues that appeared in > 1 negotiation round without resolution
- Issues that caused countries to vote `oppose`

### 6.5 Final Metrics Object

```python
@dataclass
class SimulationMetrics:
    risk_initial: float = 100.0
    risk_final: float = 0.0
    risk_reduction_pct: float = 0.0
    response_time_minutes: int = 0
    coordination_ratio: float = 0.0
    countries_coordinating: int = 0
    countries_total: int = 0
    unresolved_issues: list[str] = field(default_factory=list)
    negotiation_rounds: int = 0
    agreement_reached: bool = False
    simulation_mode: str = ""
```

---

## 7. API Specification

### Base URL: `/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scenarios` | List all available scenarios |
| GET | `/scenarios/{id}` | Get scenario details |
| GET | `/countries` | List all country profiles |
| POST | `/simulations` | Create a new simulation |
| GET | `/simulations/{id}` | Get simulation state |
| POST | `/simulations/{id}/start` | Start simulation |
| POST | `/simulations/{id}/pause` | Pause simulation |
| GET | `/simulations/{id}/metrics` | Get current metrics |
| GET | `/simulations/{id}/events` | Get event log |
| WS | `/ws/simulations/{id}` | Live event stream |
| POST | `/compare` | Run same scenario in 3 modes, return comparison |

### WebSocket Message Format

```json
{
  "type": "event | decision | negotiation | metrics | complete",
  "time_offset": 14,
  "payload": {
    "country_id": "IN",
    "event": "decision",
    "action": "share_technical_evidence",
    "reasoning": "International coordination is likely to reduce escalation risk.",
    "metrics_snapshot": {
      "risk": 55.0,
      "coordination": 0.47
    }
  }
}
```

---

## 8. Frontend Specification

### 8.1 Layout (3-panel dashboard)

```
┌─────────────┬──────────────────────────┬──────────────────┐
│   LEFT      │       CENTER             │     RIGHT        │
│   Panel     │       World Map          │   Live Feed      │
│             │                          │                  │
│ Crisis Info │  Countries with          │ AI Agent         │
│ Severity    │  color-coded status      │ decisions        │
│ Timeline    │                          │ (scrolling)      │
│             │  🔴 Unaware              │                  │
│ Current     │  🟡 Investigating        │ [country flag]   │
│ Phase       │  🔵 Notified             │ Action chosen    │
│             │  🟢 Coordinating         │ Reasoning        │
└─────────────┴──────────────────────────┴──────────────────┘
┌──────────────────────────────────────────────────────────┐
│                    METRICS BAR                           │
│  ⏱ Response: 14 min  🌐 11/15  📉 ↓63%  ⚠ 3 issues    │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Country Status Colors

| Status | Color | Meaning |
|--------|-------|---------|
| Unaware | 🔴 Red | Not yet reached by information |
| Investigating | 🟡 Yellow | Aware, gathering evidence |
| Notified | 🔵 Blue | Formally notified partners |
| Coordinating | 🟢 Green | Active participant in joint response |
| Opposing | ⚫ Gray | Blocking coordination |

### 8.3 Comparison View

Three simulation runs displayed side-by-side:

```
┌─────────────────┬─────────────────┬─────────────────┐
│ NO COORDINATION │ PARTIAL         │ COORDINATED     │
├─────────────────┼─────────────────┼─────────────────┤
│ Response: 31min │ Response: 21min │ Response: 14min │
│ Countries: 5/15 │ Countries: 9/15 │ Countries:13/15 │
│ Risk ↓: 28%     │ Risk ↓: 47%     │ Risk ↓: 76%     │
│ Issues: 7       │ Issues: 5       │ Issues: 2       │
└─────────────────┴─────────────────┴─────────────────┘

"Governance strategy changed the outcome."
```

### 8.4 Key React Components

| Component | Purpose |
|-----------|---------|
| `<CrisisHeader>` | Severity badge, title, time elapsed |
| `<WorldMap>` | Country status overlay (Leaflet/MapLibre) |
| `<LiveFeed>` | Scrolling agent decisions |
| `<MetricsBar>` | Real-time deterministic scores |
| `<NegotiationPanel>` | Proposals, votes, agreement status |
| `<ComparisonView>` | 3-mode side-by-side results |
| `<TimelineTrack>` | Event timeline with T+N markers |
| `<ScenarioSelector>` | Choose scenario and mode |

---

## 9. Tech Stack

### Backend
| Layer | Choice | Reason |
|-------|--------|--------|
| Runtime | Python 3.11 | Best AI/ML ecosystem |
| API Framework | FastAPI | Async, WebSocket support, fast |
| LLM | Anthropic Claude (claude-sonnet-4-6) | Strong reasoning, JSON mode |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Fast, local |
| Vector DB | ChromaDB | Simple, no infra required for hackathon |
| Primary DB | PostgreSQL | Relational state and logs |
| ORM | SQLAlchemy 2.0 | Async ORM |
| Task Queue | None (async FastAPI) | Sufficient for hackathon |

### Frontend
| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | React 18 + TypeScript | Type safety, component model |
| Styling | Tailwind CSS | Rapid UI iteration |
| Charts | Recharts | Clean, composable |
| Map | Leaflet + react-leaflet | Open source, flexible |
| WebSocket | native browser API | No extra deps |
| State | Zustand | Lightweight, good for streaming state |

### Infrastructure (Hackathon)
| Component | Choice |
|-----------|--------|
| Hosting | Single VM (Railway / Render / fly.io) |
| DB | Supabase free tier or local PostgreSQL |
| Vector DB | ChromaDB in-memory or local file |
| LLM API | Anthropic API (direct) |

---

## 10. Implementation Roadmap

### Phase 0 — Foundation (Days 1–2)

- [ ] Initialize repo (monorepo: `/backend`, `/frontend`, `/data`)
- [ ] Set up FastAPI with health check endpoint
- [ ] Set up PostgreSQL schema (see Section 3.4)
- [ ] Initialize React + TypeScript + Tailwind project
- [ ] Create 3 country profiles (JSON)
- [ ] Create 1 crisis scenario (YAML)
- [ ] Verify Anthropic API connectivity
- [ ] Create basic simulation engine skeleton

**Milestone:** Backend starts, returns mock simulation data to frontend.

---

### Phase 1 — Core Simulation (Days 3–4)

- [ ] Implement simulation clock and event engine
- [ ] Implement information spread logic (delay per country)
- [ ] Implement 3 country agents (LLM-backed with prompt templates)
- [ ] Implement international coordinator agent
- [ ] Wire up action → risk score reduction (deterministic)
- [ ] Implement response time and coordination score calculations
- [ ] WebSocket endpoint for live event streaming
- [ ] Basic React dashboard: left panel + live feed

**Milestone:** One simulation runs end-to-end, events stream to frontend.

---

### Phase 2 — RAG + Governance Knowledge (Days 4–5)

- [ ] Collect/write 5–8 governance documents (PDF or text)
- [ ] Chunk and embed documents with sentence-transformers
- [ ] Load into ChromaDB
- [ ] Integrate RAGEngine into agent prompt assembly
- [ ] Verify RAG improves decision quality (spot check)

**Milestone:** Agents reference real governance frameworks in reasoning.

---

### Phase 3 — Full Dashboard (Days 5–6)

- [ ] World map with country status color coding
- [ ] Real-time metrics bar (risk, response time, coordination, issues)
- [ ] Negotiation panel (proposals, vote tallies)
- [ ] Timeline track (T+0 to T+N events)
- [ ] Expand to 15 country profiles
- [ ] Add 3 crisis scenarios

**Milestone:** Full live dashboard running with 15 countries.

---

### Phase 4 — Comparison Mode (Day 6–7)

- [ ] Implement 3 simulation modes:
  - `no_coordination`: agents cannot communicate, no joint actions
  - `partial_coordination`: bilateral only, no multilateral
  - `coordinated`: full international coordinator enabled
- [ ] `/compare` endpoint: run same scenario in all 3 modes sequentially
- [ ] Comparison view UI component

**Milestone:** Demo-ready comparison showing governance strategy impact.

---

### Phase 5 — Polish & Demo Prep (Day 7)

- [ ] Add 2 additional crisis scenarios for variety
- [ ] Smooth animations for live feed and map transitions
- [ ] Error handling and graceful degradation
- [ ] Seed database with 1 pre-run comparison result (fast demo path)
- [ ] Record backup demo video in case of live API issues
- [ ] README and architecture diagram

**Milestone:** Hackathon submission ready.

---

### Optional Enhancements (If Time Permits)

- [ ] Scenario generator (randomized parameters)
- [ ] Export simulation results to JSONL (training data format)
- [ ] Country agent personality tuning via sliders (UI)
- [ ] Replay mode (step through a completed simulation)

---

## 11. Folder Structure

```
ai-governance-simulator/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app entrypoint
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── scenarios.py
│   │   │   │   ├── simulations.py
│   │   │   │   └── compare.py
│   │   │   └── websocket.py
│   │   ├── simulation/
│   │   │   ├── engine.py             # SimulationEngine
│   │   │   ├── events.py             # Event timeline
│   │   │   ├── state.py              # SimulationState
│   │   │   └── information.py        # Info spread logic
│   │   ├── agents/
│   │   │   ├── country_agent.py      # Per-country LLM agent
│   │   │   ├── coordinator_agent.py  # International coordinator
│   │   │   ├── orchestrator.py       # Agent orchestration
│   │   │   └── prompts.py            # Prompt templates
│   │   ├── rag/
│   │   │   ├── engine.py             # RAGEngine
│   │   │   ├── embedder.py           # Sentence transformer wrapper
│   │   │   └── loader.py             # Document ingestion
│   │   ├── scoring/
│   │   │   └── metrics.py            # Deterministic scoring
│   │   ├── models/
│   │   │   ├── db.py                 # SQLAlchemy models
│   │   │   └── schemas.py            # Pydantic schemas
│   │   └── core/
│   │       ├── config.py             # Settings (env vars)
│   │       └── database.py           # DB connection
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CrisisHeader.tsx
│   │   │   ├── WorldMap.tsx
│   │   │   ├── LiveFeed.tsx
│   │   │   ├── MetricsBar.tsx
│   │   │   ├── NegotiationPanel.tsx
│   │   │   ├── ComparisonView.tsx
│   │   │   ├── TimelineTrack.tsx
│   │   │   └── ScenarioSelector.tsx
│   │   ├── store/
│   │   │   └── simulationStore.ts    # Zustand state
│   │   ├── hooks/
│   │   │   └── useSimulationSocket.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── App.tsx
│   ├── package.json
│   └── tailwind.config.js
│
├── data/
│   ├── countries/
│   │   ├── country_alpha.json
│   │   ├── country_beta.json
│   │   └── ...
│   ├── scenarios/
│   │   ├── crisis_001.yaml
│   │   ├── crisis_002.yaml
│   │   └── crisis_003.yaml
│   └── governance/
│       ├── ai_principles.pdf
│       ├── incident_response.pdf
│       └── international_cooperation.pdf
│
├── scripts/
│   ├── ingest_documents.py           # Load docs into ChromaDB
│   ├── generate_scenario.py          # Random scenario generator
│   └── export_training_data.py       # Export simulation logs
│
└── README.md
```

---

## 12. Future Enhancements

### Short-Term (Post-Hackathon v1.1)

- Fine-tuning pipeline: collect simulation logs → train small model on (situation, decision, outcome) triples
- More scenario types: disinformation crisis, AI weapons proliferation, autonomous system accident
- Human-in-the-loop mode: user plays as one country agent

### Medium-Term (v2.0)

- Persistent scenario library with community contributions
- Historical comparison: map simulated decisions to real-world governance responses
- Multilingual agent responses (simulate language/translation barriers)
- Economic impact modeling integrated into risk scoring

### Long-Term (Research Track)

- Generate 10,000+ simulations → analyze which governance structures statistically perform best
- Publish dataset as open research resource
- Partner with policy institutes for validated governance frameworks

---

## Appendix A — Deterministic Scoring Reference

| Metric | Formula | Unit |
|--------|---------|------|
| Risk Final | `max(0, 100 + Σ(action_values) × (1 - 0.2 × coord))` | 0–100 |
| Risk Reduction | `(100 - risk_final) / 100` | % |
| Response Time | `coordinated_action_time - detection_time` | minutes |
| Coordination | `approving_countries / total_countries` | 0.0–1.0 |
| Unresolved Issues | Count of issues in >1 negotiation round | count |

---

## Appendix B — Example End-State Comparison

| Metric | No Coordination | Partial | Coordinated |
|--------|----------------|---------|-------------|
| Response Time | 31 min | 21 min | 14 min |
| Countries Active | 5/15 | 9/15 | 13/15 |
| Risk Reduction | 28% | 47% | 76% |
| Unresolved Issues | 7 | 5 | 2 |
| Agreement Reached | ✗ | Partial | ✓ |

> **"Governance strategy changed the outcome."**

---

*Document version 1.0 — AI Governance Crisis Simulator*

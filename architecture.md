# Architecture — AI Governance Crisis Simulator

## 1. Core Concept

The system is a **software simulation platform**, not a trained model. An existing LLM acts as a reasoning/negotiation engine on top of structured data your system supplies: country profiles, crisis scenarios, governance rules, timelines, and deterministic scoring.

```
Scenario → Countries/Organizations → Information delays →
Decisions → Negotiation → Response → AI evaluation
```

No custom model training is required for v1.

---

## 2. High-Level System Diagram

```
                 React Frontend
                       │
                       ▼
                  FastAPI API
                       │
              ┌────────┴────────┐
              │                 │
        Simulation Engine     RAG
              │                 │
              │           Vector Database
              │                 │
              │        Governance Documents
              │
       ┌──────┴───────┐
       │              │
   Country Agents   Crisis Agent
       │              │
       └──────┬───────┘
              │
         Negotiation
              │
              ▼
          Evaluator
              │
              ▼
       Metrics Engine
              │
              ▼
          Dashboard
```

---

## 3. Component Breakdown

### 3.1 Crisis Engine
Central orchestrator. Owns the simulation clock/timeline and drives state transitions for every country as the crisis unfolds.

```
                    CRISIS
                       │
                       ▼
              ┌─────────────────┐
              │ Crisis Engine   │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   🇺🇸 Agent        🇮🇳 Agent        🇪🇺 Agent
   Security        Sovereignty      Regulation
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              🌐 International
                 Coordinator
                       │
                       ▼
                Negotiation
                       │
                       ▼
                 Final Action
```

- Not every country needs a real LLM call. Lightweight/rule-based agents can represent minor actors; LLM calls are reserved for meaningful reasoning or negotiation moments.

### 3.2 Country Agents
Each agent wraps an LLM call scoped to a single country's profile, current information state, and available actions. Output is parsed into a structured decision object (`action`, `rationale`, `risk_note`).

### 3.3 International Coordinator
A synthesis agent that reviews all country positions, proposes a joint response, and manages voting rounds until agreement, partial agreement, or breakdown.

### 3.4 RAG (Retrieval-Augmented Generation) Layer
Grounds agent reasoning in real governance material instead of pure LLM improvisation.

```
User/System
     ↓
Question
     ↓
Retriever
     ↓
Relevant governance documents
     ↓
LLM
     ↓
Decision
```

Documents live in a vector database (e.g., pgvector, Chroma, FAISS) and are retrieved per-decision, not memorized.

### 3.5 Metrics / Evaluator Engine
Deterministic, code-driven scoring — never delegated to the LLM. See `rules.md` for the exact formulas.

### 3.6 Dashboard
Live frontend visualization of crisis status, country map, agent decisions, and metrics. See `design.md` for layout.

---

## 4. Data Architecture

```
/data
   /governance
       ai_principles.pdf
       incident_response.pdf
       international_cooperation.pdf

   /countries
       country_a.json
       country_b.json

   /scenarios
       crisis_001.json
       crisis_002.json
```

### Country Profile Schema
```json
{
  "country": "Country_A",
  "priorities": ["national_security", "economic_stability", "AI_development"],
  "risk_tolerance": "medium",
  "transparency": "medium",
  "coordination": "high",
  "decision_speed": "fast"
}
```

### Scenario Schema
```yaml
title: Cross-Border AI Infrastructure Failure
severity: critical
affected_countries: 15
initial_detection:
  country: Country_A
  source: AI monitoring system
information_delay:
  Country_A: 0
  Country_B: 5
  Country_C: 8
  Country_D: 12
potential_impacts:
  - infrastructure
  - financial_markets
  - public_services
possible_actions:
  - investigate
  - notify
  - temporarily suspend system
  - international audit
  - public warning
```

---

## 5. Prompt-to-Decision Flow

```
Existing LLM
     ↓
System prompt
     ↓
Country profile
     ↓
Crisis state
     ↓
Retrieved governance documents
     ↓
Decision
```

Example conceptual prompt payload:
```
You are the AI advisor for Country A.
Country priorities: national security, economic stability, international cooperation
Current crisis: Cross-border AI infrastructure failure
Current information: Only 40% verified
Other countries: Country B has not confirmed the incident; Country C is requesting evidence
Available actions: Investigate, Notify, Suspend, Share evidence, Request international meeting
Recommend the next action. Explain: (1) why, (2) risks, (3) expected international reaction.
```

---

## 6. Event Timeline Engine

The crisis unfolds on a tick-based clock independent of the LLM:

```
T+00 → Incident detected
T+03 → Country A verifies anomaly
T+05 → Country B receives partial information
T+08 → Social media reports incident
T+11 → Country C requests clarification
T+14 → International alert issued
T+18 → Emergency meeting
T+25 → Countries negotiate response
T+32 → Joint action approved
```

The frontend subscribes to this stream (WebSocket preferred; polling as fallback) to render the crisis live.

---

## 7. Recommended Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React + TypeScript | Tailwind CSS, Recharts, Leaflet/MapLibre |
| Backend | FastAPI (Python) | Easiest ecosystem for AI/RAG; Spring Boot is a fallback if staying in Java |
| Database | PostgreSQL (or SQLite for hackathon speed) | Stores runs, metrics, scenario history |
| Vector Store | pgvector / Chroma / FAISS | For RAG over governance documents |
| Realtime | WebSocket | Drives live dashboard updates |

Recommended combination for this project: **React + FastAPI + PostgreSQL**, since the AI/simulation ecosystem is easier in Python.

---

## 8. Extensibility: Levels of "Training"

| Level | Approach | Use in v1? |
|---|---|---|
| 1 | Prompt-based simulation (profiles + scenarios + rules + prompts) | ✅ Core of v1 |
| 2 | RAG over governance documents | ✅ Recommended for v1 |
| 3 | Fine-tuning on simulation-generated `{situation → decision → outcome}` data | ❌ Future work only |

A scenario generator (randomizing severity, delays, country count, conflicting priorities) can later produce a `crisis_training_dataset.jsonl` of simulation records — useful as evaluation data and a stepping stone toward Level 3, but not required to ship v1.

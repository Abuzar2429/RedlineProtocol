# Product Requirements Document
# AI Governance Crisis Simulator

---

| Field | Detail |
|-------|--------|
| **Document Status** | Draft v1.0 |
| **Product Name** | AI Governance Crisis Simulator |
| **Document Owner** | Product Team |
| **Last Updated** | September 2026 |
| **Target Release** | Hackathon MVP |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [User Personas](#4-user-personas)
5. [Scope](#5-scope)
6. [User Stories & Requirements](#6-user-stories--requirements)
7. [Functional Requirements](#7-functional-requirements)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [UX & Design Requirements](#9-ux--design-requirements)
10. [Data Requirements](#10-data-requirements)
11. [AI & Model Requirements](#11-ai--model-requirements)
12. [Dependencies & Constraints](#12-dependencies--constraints)
13. [Risks & Mitigations](#13-risks--mitigations)
14. [Open Questions](#14-open-questions)
15. [Out of Scope](#15-out-of-scope)
16. [Acceptance Criteria](#16-acceptance-criteria)

---

## 1. Executive Summary

AI Governance Crisis Simulator is a multi-agent simulation platform that models how nations and international organizations respond to AI-related crises. It uses large language models as reasoning engines for country-specific AI agents, deterministic scoring to quantify outcomes, and a real-time dashboard to visualize negotiation, decision-making, and coordination as they unfold.

The platform's primary demonstration is compelling and empirically grounded: **the same crisis, governed under different coordination strategies, produces measurably different outcomes.** Running three simulations of identical crises — with no coordination, partial coordination, and full coordination — yields quantified differences in response time, risk reduction, and international alignment.

The core innovation is the simulation architecture itself, not the underlying AI model. The platform supplies structure; the LLM supplies reasoning within that structure.

---

## 2. Problem Statement

### 2.1 The Real-World Gap

International AI governance is currently reactive and fragmented. When an AI-related incident occurs across borders, no universal playbook exists. Nations have conflicting priorities, receive information at different times, and make decisions in isolation — often making situations worse through incoordination.

There is no low-risk environment to:
- Test governance frameworks before a real crisis hits
- Understand how information asymmetry degrades collective response
- Compare the measurable impact of different coordination architectures
- Train policymakers and researchers in governance decision-making

### 2.2 The Product Gap

Existing AI governance tools are primarily:
- **Static documents** (principles, frameworks, whitepapers) — not interactive
- **Tabletop exercises** — expensive, infrequent, human-run, hard to repeat
- **Chatbots** that answer governance questions — no simulation capability
- **Academic models** — not accessible to non-technical stakeholders

### 2.3 What This Product Solves

The simulator provides a repeatable, quantifiable, interactive environment where:
- AI agents representing nations reason from real governance frameworks
- Crises unfold dynamically with information delays and escalation
- Outcomes are scored deterministically (not hallucinated)
- Different governance strategies can be compared side-by-side in minutes

---

## 3. Goals & Success Metrics

### 3.1 Product Goals

| # | Goal |
|---|------|
| G1 | Demonstrate that coordination strategy measurably changes crisis outcomes |
| G2 | Simulate a 15-country AI crisis with realistic information asymmetry |
| G3 | Produce live, real-time visual output suitable for a compelling hackathon demo |
| G4 | Generate deterministic, defensible metrics — not LLM-generated numbers |
| G5 | Run the same crisis in 3 modes and show the comparison in a single screen |

### 3.2 Success Metrics (MVP / Hackathon)

| Metric | Target |
|--------|--------|
| End-to-end simulation runs without error | 100% of demo attempts |
| Time for a single simulation to complete | < 3 minutes wall-clock |
| Countries modeled per simulation | 15 |
| Crisis scenarios available | ≥ 3 |
| Metrics computed deterministically | 4 of 4 (risk, time, coordination, issues) |
| Live WebSocket event delivery latency | < 500ms per event |
| Comparison view shows 3-mode results | ✓ |
| Dashboard renders on 1920×1080 without scroll | ✓ |

### 3.3 Non-Goals for This Version

- Predicting real-world policy outcomes
- Being a certified training tool for actual policymakers
- Achieving research-grade accuracy in geopolitical modeling

---

## 4. User Personas

### Persona 1 — Hackathon Judge / Technical Evaluator

**Who:** Senior engineer or AI researcher evaluating projects at a hackathon.

**What they care about:**
- Is the technical architecture novel and defensible?
- Does the AI do something genuinely interesting — not just a wrapper?
- Are the numbers produced trustworthy or hallucinated?
- Can I understand the system quickly from a demo?

**What they need from the product:**
- A clear, impressive live demo under 5 minutes
- Visible AI reasoning (not a black box)
- Quantitative outputs with a clear methodology
- A compelling comparison that shows the "so what"

---

### Persona 2 — Policy Researcher / Domain Expert

**Who:** Someone working on AI governance, international relations, or tech policy.

**What they care about:**
- Do the agents reason from real governance frameworks?
- Are country profiles grounded in recognizable behavioral patterns?
- Does the platform surface dynamics that match real-world challenges (info asymmetry, veto players, trust deficits)?

**What they need from the product:**
- Visible reasoning from governance documents
- Configurable country priorities
- Multiple scenarios with different structural dynamics

---

### Persona 3 — Builder / Teammate

**Who:** The developer and team member building and maintaining the system.

**What they care about:**
- Clear modular architecture
- Fast iteration cycle
- Reliable demo path with fallback options
- No surprise API costs at demo time

**What they need from the product:**
- Seeded demo state (preloaded simulation that can replay instantly)
- Clean separation between simulation engine, agents, and frontend
- Configurable LLM call frequency (throttle to save cost)

---

## 5. Scope

### 5.1 In Scope — MVP

| Area | Features Included |
|------|------------------|
| Simulation Engine | Event clock, information spread, state machine, 3 coordination modes |
| AI Agents | 15 country agents (LLM-backed), 1 international coordinator agent |
| Governance RAG | 5–8 governance documents ingested and retrievable per agent prompt |
| Scoring | Deterministic: risk score, response time, coordination ratio, unresolved issues |
| Dashboard | 3-panel layout: crisis info, world map, live agent feed; metrics bar |
| Scenarios | 3 pre-built crisis scenarios |
| Comparison Mode | Run same scenario in 3 coordination modes, render side-by-side results |
| API | REST endpoints for scenario/simulation management; WebSocket for live events |

### 5.2 Out of Scope — MVP

See [Section 15](#15-out-of-scope) for full list.

---

## 6. User Stories & Requirements

### Epic 1: Simulation Setup

**US-01** — As a user, I want to select a crisis scenario from a list, so I can choose what kind of incident to simulate.

**US-02** — As a user, I want to select a coordination mode (no coordination / partial / full), so I can test different governance approaches.

**US-03** — As a user, I want to start a simulation with one click after selecting scenario and mode.

**US-04** — As a user, I want to run a 3-way comparison of the same scenario under all coordination modes at once, so I can see the full contrast without setting up each simulation manually.

---

### Epic 2: Live Simulation Visualization

**US-05** — As a user, I want to see a world map showing which countries are aware of the crisis and at what status, so I can understand information spread in real time.

**US-06** — As a user, I want to see a live feed of AI agent decisions as they happen, with the country, action taken, and reasoning, so I understand what each nation is doing and why.

**US-07** — As a user, I want to see the crisis timeline (T+0, T+5, T+8…) as events unfold, so I understand the pace and sequence of the simulation.

**US-08** — As a user, I want to see the current negotiation proposal and how countries are voting on it, so I can follow the international coordination dynamics.

---

### Epic 3: Metrics & Outcomes

**US-09** — As a user, I want to see real-time metrics (risk level, coordination ratio, response time, unresolved issues) updating as the simulation progresses.

**US-10** — As a user, I want a final summary screen at the end of the simulation showing all metrics and the joint agreement (if reached).

**US-11** — As a user, I want to see the 3-mode comparison table with one headline statement ("governance strategy changed the outcome"), so I can quickly communicate the value to others.

---

### Epic 4: Agent Transparency

**US-12** — As a user, I want to read the full reasoning of any country agent's decision by clicking on it, so I can understand the AI's logic.

**US-13** — As a user, I want to see which governance documents an agent referenced when making a decision (RAG source attribution), so I trust the reasoning is grounded.

---

## 7. Functional Requirements

### 7.1 Simulation Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | The engine shall maintain a simulation clock in minutes, advancing discretely | Must |
| FR-02 | Each country shall receive crisis information at a configurable time offset from T+0 | Must |
| FR-03 | Evidence completeness per country shall grow over time at a configurable rate | Must |
| FR-04 | The engine shall emit events at predefined time offsets (detection, spread, media, negotiation, resolution) | Must |
| FR-05 | The engine shall support 3 coordination modes affecting which actions and channels are available | Must |
| FR-06 | The engine shall run without blocking the API (async) | Must |
| FR-07 | A simulation shall reach a terminal state (agreement or timeout) within a bounded number of ticks | Must |
| FR-08 | Simulation state shall be persisted to the database for replay and audit | Should |

### 7.2 Country Agents

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-09 | Each country agent shall be initialized from a JSON profile specifying priorities, risk tolerance, and decision speed | Must |
| FR-10 | Each country agent shall receive a structured prompt including: its profile, current crisis state, its own evidence completeness, other countries' known positions, and RAG-retrieved governance context | Must |
| FR-11 | Each country agent shall return a structured JSON response: action, reasoning, risks, expected reactions, willingness to coordinate | Must |
| FR-12 | Country agents with `decision_speed: fast` and low influence may use rule-based responses instead of LLM calls to reduce latency and cost | Should |
| FR-13 | Each agent shall only be prompted when it has new information or is participating in a negotiation round | Must |

### 7.3 International Coordinator Agent

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-14 | The coordinator agent shall activate when ≥ 50% of affected countries are aware and at least one multilateral action is available | Must |
| FR-15 | The coordinator shall synthesize all country positions into a joint proposal | Must |
| FR-16 | The coordinator shall predict which countries will approve, oppose, or abstain | Must |
| FR-17 | The coordinator shall identify and list unresolved issues blocking consensus | Must |
| FR-18 | Multiple negotiation rounds shall be supported until agreement is reached or timeout occurs | Must |

### 7.4 RAG Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-19 | The system shall ingest a minimum of 5 governance documents into a vector database at startup | Must |
| FR-20 | The RAG engine shall retrieve the top 5 most relevant document chunks per agent prompt | Must |
| FR-21 | Retrieved document titles and IDs shall be included in the agent's response metadata for attribution | Should |
| FR-22 | Document ingestion shall be idempotent (re-running ingest shall not duplicate chunks) | Should |

### 7.5 Scoring & Metrics

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-23 | Risk score shall be computed deterministically from a defined action-to-reduction map and coordination multiplier | Must |
| FR-24 | Response time shall be computed as `coordinated_action_time - detection_time` in minutes | Must |
| FR-25 | Coordination ratio shall be computed as `approving_countries / total_countries` | Must |
| FR-26 | Unresolved issues shall be counted from issues appearing in > 1 negotiation round without resolution | Must |
| FR-27 | No metric value shall be taken from LLM output without deterministic validation | Must |

### 7.6 API

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-28 | REST endpoints shall exist for: listing scenarios, creating a simulation, starting/pausing, fetching state, fetching metrics, fetching event log | Must |
| FR-29 | A WebSocket endpoint shall stream simulation events to connected clients in real time | Must |
| FR-30 | A `/compare` endpoint shall run one scenario in all 3 modes sequentially and return a unified comparison object | Must |
| FR-31 | All REST responses shall use a consistent JSON envelope with `status`, `data`, and `error` fields | Should |

### 7.7 Frontend

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-32 | The dashboard shall use a 3-panel layout: left (crisis info + timeline), center (world map), right (live agent feed) | Must |
| FR-33 | The world map shall color-code countries by status: unaware (red), investigating (yellow), notified (blue), coordinating (green), opposing (gray) | Must |
| FR-34 | The live feed shall display agent decisions as they arrive via WebSocket, newest on top | Must |
| FR-35 | A metrics bar shall display 4 live metrics below the 3-panel layout, updating in real time | Must |
| FR-36 | A negotiation panel shall display the current proposal, vote tallies, and unresolved issues | Must |
| FR-37 | A comparison view shall render a 3-column table of metric outcomes, with a headline statement | Must |
| FR-38 | Clicking any agent decision in the live feed shall expand it to show full reasoning and RAG sources | Should |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-01 | A single simulation (15 countries, 1 scenario) shall complete within 3 minutes wall-clock time |
| NFR-02 | WebSocket event delivery shall have < 500ms latency from engine tick to client render |
| NFR-03 | The frontend dashboard shall render at 60fps during live simulation (no layout jank) |
| NFR-04 | API cold start shall be < 10 seconds (including RAG index load) |

### 8.2 Reliability

| ID | Requirement |
|----|-------------|
| NFR-05 | If an LLM API call fails, the agent shall fall back to a rule-based default action rather than crashing |
| NFR-06 | A simulation shall never enter an infinite loop; a maximum tick count (e.g. 120 ticks) shall terminate it |
| NFR-07 | The system shall have a pre-seeded demo simulation that can replay without API calls, as a fallback |

### 8.3 Security

| ID | Requirement |
|----|-------------|
| NFR-08 | The Anthropic API key shall not be exposed in frontend code or API responses |
| NFR-09 | No personally identifiable information shall be stored or transmitted |
| NFR-10 | All API endpoints shall validate input schema via Pydantic before processing |

### 8.4 Scalability (Post-MVP)

| ID | Requirement |
|----|-------------|
| NFR-11 | The architecture shall support running multiple simulations concurrently without state collision |
| NFR-12 | The vector database shall be replaceable with a managed service (e.g. Pinecone) without changing the RAG interface |

### 8.5 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-13 | Adding a new country profile shall require only creating a new JSON file — no code changes |
| NFR-14 | Adding a new scenario shall require only creating a new YAML file — no code changes |
| NFR-15 | Agent prompt templates shall be maintained in a single `prompts.py` file, not scattered across agent classes |

---

## 9. UX & Design Requirements

### 9.1 Design Principles

**Clarity over density.** The dashboard must be legible at a glance. Judges viewing from 3 feet away must understand what's happening.

**Live, not static.** Every part of the UI should respond to simulation events. A dashboard that looks the same as when it started is a failed demo.

**Numbers you can trust.** All displayed metrics must have a visible, simple derivation. "11/15 countries coordinating" is better than "73.3% coordination index."

**Drama without noise.** The crisis is serious; the UI should convey urgency without being garish. Dark theme, high-contrast status indicators, minimal decoration.

### 9.2 Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  🚨 AI GOVERNANCE CRISIS SIMULATOR           [Scenario] [Mode]   │
├────────────────┬───────────────────────────┬────────────────────┤
│ CRISIS STATUS  │       WORLD MAP           │   LIVE DECISIONS   │
│                │                           │                    │
│ 🔴 CRITICAL    │  [Interactive map with    │  🇮🇳 Country India  │
│                │   country markers]        │  Action: Share     │
│ AI Infra       │                           │  evidence          │
│ Incident       │  🔴 Unaware               │  ──────────────    │
│                │  🟡 Investigating         │  🇩🇪 Country DE    │
│ Severity       │  🔵 Notified             │  Action: Request   │
│ ████████░ 91%  │  🟢 Coordinating          │  joint audit       │
│                │  ⚫ Opposing              │  ──────────────    │
│ TIMELINE       │                           │  🌐 Coordinator    │
│ ✓ T+00 Detect  │                           │  Proposal:         │
│ ✓ T+03 Verify  │                           │  Containment +     │
│ ✓ T+05 Spread  │                           │  Joint Invest.     │
│ ● T+14 Meeting │                           │  Votes: 9/15       │
│ ○ T+25 Agree   │                           │                    │
├────────────────┴───────────────────────────┴────────────────────┤
│  ⏱ 14 min    🌐 11/15 countries    📉 Risk ↓63%    ⚠ 3 issues  │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 Color System

| Element | Color | Hex |
|---------|-------|-----|
| Background | Near-black | `#0D1117` |
| Panel background | Dark gray | `#161B22` |
| Border | Subtle gray | `#30363D` |
| Critical severity | Red | `#F85149` |
| High severity | Orange | `#DB6D28` |
| Unaware status | Red | `#F85149` |
| Investigating | Amber | `#E3B341` |
| Notified | Blue | `#388BFD` |
| Coordinating | Green | `#3FB950` |
| Opposing | Gray | `#6E7681` |
| Metrics accent | Teal | `#79C0FF` |
| Text primary | White | `#F0F6FC` |
| Text secondary | Gray | `#8B949E` |

### 9.4 Typography

- Headings: `Inter` or system sans-serif, bold
- Body / labels: `Inter`, regular
- Monospace (agent reasoning, JSON): `JetBrains Mono` or `Fira Code`
- Font sizes: 11px (metadata), 13px (body), 15px (labels), 20px (headings), 28px (big metrics)

### 9.5 Animation Requirements

| Interaction | Animation |
|-------------|-----------|
| New agent decision arriving | Slide in from right, fade in |
| Country status change on map | Marker pulses once, color transitions over 300ms |
| Metrics updating | Number counts up/down over 500ms |
| Negotiation vote tally | Bar fills left to right |
| Crisis severity bar | Animated on load; static during sim |
| Timeline event completing | Checkmark appears with brief green flash |

---

## 10. Data Requirements

### 10.1 Country Profiles

- Minimum 15 country profiles required for MVP
- Each profile stored as a JSON file in `/data/countries/`
- Countries must span diverse geopolitical blocs (Western, BRICS, Global South, island/small states)
- No real country names used — anonymized as Country Alpha, Country Beta, etc. (to avoid political sensitivity in demo)

### 10.2 Crisis Scenarios

- Minimum 3 scenarios required for MVP
- Scenarios stored as YAML files in `/data/scenarios/`
- Scenarios must vary on: severity (medium / high / critical), number of countries affected (8, 12, 15), and primary impact domain (infrastructure, financial, public safety)

**Required Scenario Types:**

| ID | Title | Severity | Countries |
|----|-------|----------|-----------|
| crisis_001 | Cross-Border AI Infrastructure Failure | Critical | 15 |
| crisis_002 | Autonomous Decision System Discrimination | High | 10 |
| crisis_003 | AI-Enabled Market Manipulation | High | 12 |

### 10.3 Governance Documents

- Minimum 5 documents required, covering:
  - AI principles and ethics frameworks
  - International incident response procedures
  - Data sharing and sovereignty agreements
  - Emergency AI system shutdown protocols
  - Cross-border liability frameworks
- Documents may be synthesized (written by the team) for hackathon purposes to avoid copyright issues
- All documents chunked at 500 tokens with 50-token overlap

### 10.4 Simulation Logs

All simulation runs stored in PostgreSQL including: full event log, all agent decisions with prompts and responses, negotiation rounds, final metrics. Retention: indefinite for MVP (small data volume).

---

## 11. AI & Model Requirements

### 11.1 LLM Usage

| Use Case | Model | Call Frequency |
|----------|-------|----------------|
| Country agent decisions | `claude-sonnet-4-6` | Per decision point, per aware country |
| International coordinator | `claude-sonnet-4-6` | Per negotiation round |
| Rule-based fallback (low-influence countries) | None | N/A |

### 11.2 Prompt Requirements

| Requirement | Detail |
|-------------|--------|
| Max prompt length | 4,000 tokens (to stay within cost budget) |
| Response format | JSON-only; no markdown or preamble |
| Temperature | 0.7 for country agents (some variance), 0.3 for coordinator (more deterministic) |
| Retry policy | 1 retry on failure, then rule-based fallback |
| Cost guard | Maximum 50 LLM calls per simulation run |

### 11.3 What the LLM Must NOT Do

- Generate metric values (risk score, response time, coordination ratio) — these are computed deterministically
- Invent governance documents or cite non-existent sources
- Make decisions that are impossible given a country's information state (engine enforces this structurally)
- Break out of the JSON response schema (validated via Pydantic before use)

### 11.4 Embeddings

- Model: `sentence-transformers/all-MiniLM-L6-v2` (local, no API cost)
- Vector DB: ChromaDB (local or in-memory for MVP)
- Embedding dimension: 384
- Similarity metric: cosine

---

## 12. Dependencies & Constraints

### 12.1 External Dependencies

| Dependency | Purpose | Risk if Unavailable |
|------------|---------|---------------------|
| Anthropic API | LLM reasoning for agents | High — fallback to rule-based only |
| ChromaDB | Vector storage for RAG | Medium — can use in-memory mode |
| PostgreSQL | Simulation state persistence | Medium — can use SQLite for demo |
| Leaflet / MapLibre | World map rendering | Low — can substitute with SVG grid |

### 12.2 Budget Constraints

- Anthropic API: target < $5 total for all demo runs
- Cloud hosting: free tier only (Railway, Render, or fly.io)
- All other dependencies: open source / free tier

### 12.3 Timeline Constraint

- Full MVP must be demo-ready in 7 days
- Phases 0–2 are blocking for Phase 3+; no parallel critical paths

### 12.4 Team Constraints

- Assumes 2–3 developers
- Frontend and backend can be developed in parallel after Phase 0 establishes the WebSocket contract

---

## 13. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM API outage during demo | Low | Critical | Pre-seed a completed simulation replay; demo from stored state |
| LLM responses don't parse as valid JSON | Medium | High | Wrap all LLM calls in JSON validation; retry once; fall back to rule-based action |
| API cost exceeds budget | Medium | Medium | Cap at 50 LLM calls per simulation; use rule-based for low-influence countries |
| Simulation runs too slowly for live demo | Medium | High | Compress simulation ticks (1 tick = 500ms real time); pre-run comparison in background |
| RAG retrieval returns irrelevant chunks | Medium | Medium | Manually verify top-5 results for each scenario-country pair during testing |
| World map library has rendering issues | Low | Low | Fallback to a simple HTML/CSS grid of country cards |
| WebSocket connection drops mid-demo | Low | High | Implement auto-reconnect; show last-known state while reconnecting |
| Scope creep kills MVP | High | High | Any feature not in Phase 0–4 is automatically deferred; no exceptions during build week |

---

## 14. Open Questions

| # | Question | Owner | Due |
|---|----------|-------|-----|
| OQ-01 | Do we use real country names in the demo or anonymized ones? Consider political sensitivity with judges from different regions. | Product | Day 1 |
| OQ-02 | Should country agents be allowed to form bilateral alliances mid-simulation, or only multilateral responses through the coordinator? | Engineering | Day 2 |
| OQ-03 | What is the right tick rate for a compelling live demo? Too fast = hard to follow; too slow = boring. Recommend testing 1 tick per 800ms. | Engineering | Day 3 |
| OQ-04 | Should the comparison mode run all 3 simulations in sequence (3× slower) or run them concurrently? Concurrent is faster but adds complexity. | Engineering | Day 2 |
| OQ-05 | How should we handle a scenario where no agreement is reached? Show a "governance failure" outcome with its own metrics? | Product | Day 2 |
| OQ-06 | Are synthesized governance documents acceptable, or should we use real OECD / UN documents (with attribution)? | Legal/Product | Day 1 |
| OQ-07 | Should the hackathon demo allow the user to change scenario parameters (severity, countries) or just pick from a fixed list? | Product | Day 1 |

---

## 15. Out of Scope

The following are explicitly excluded from the MVP and should not be built during the hackathon:

| Feature | Reason for Exclusion |
|---------|---------------------|
| User authentication / accounts | Not required for single-demo context |
| Human-in-the-loop mode (user plays as a country) | Adds interaction complexity; MVP is automated |
| Fine-tuning a custom model | Not feasible in 7 days; LLM prompt engineering is sufficient |
| Mobile-responsive design | Dashboard is for desktop demo only |
| Multi-language support | English only for MVP |
| Scenario builder UI | Scenarios configured via YAML files only |
| Economic impact modeling | Out of scope for governance layer |
| Export to PDF / report generation | Not required for demo |
| Replay controls (scrub, rewind) | Play-forward only for MVP |
| Multilateral treaty database integration | Synthesized documents sufficient |
| Real-world data feeds (news, social media) | All data is simulated |
| Country agent parameter sliders in UI | JSON profile editing only |

---

## 16. Acceptance Criteria

A simulation run is considered **complete and acceptable** when all of the following are true:

### Simulation Engine
- [ ] Simulation runs from T+0 to final state without unhandled exceptions
- [ ] All 15 countries receive information at the correct offset times
- [ ] At least one negotiation round occurs before termination
- [ ] Terminal state is reached (agreement, partial agreement, or timeout) within 60 ticks

### AI Agents
- [ ] Each LLM-backed agent returns valid JSON matching the response schema
- [ ] Agent reasoning references at least one retrieved governance document
- [ ] No agent takes an action it cannot take given its current information state
- [ ] Rule-based fallback activates on LLM failure without crashing the simulation

### Metrics
- [ ] Risk score changes deterministically based on actions taken (verified by test)
- [ ] Response time is calculated from actual event timestamps, not LLM output
- [ ] Coordination ratio equals `approving_countries / total_countries` exactly
- [ ] No metric value is taken from unvalidated LLM text

### Frontend
- [ ] World map renders all 15 country markers with correct initial state
- [ ] Country status colors update in real time via WebSocket
- [ ] Live feed displays agent decisions as they arrive, with flag + action + reasoning
- [ ] Metrics bar updates after each significant simulation event
- [ ] Comparison view renders all 3 modes side-by-side after a compare run
- [ ] Dashboard is fully visible on a 1920×1080 monitor without scrolling

### Demo Path
- [ ] A complete demo (scenario select → simulate → results) runs in under 5 minutes
- [ ] Pre-seeded replay state is available as a fallback if API fails
- [ ] The comparison headline ("governance strategy changed the outcome") is displayed prominently

### Data
- [ ] 3 crisis scenarios are available and selectable
- [ ] 15 country profiles are loaded at startup
- [ ] Minimum 5 governance documents are indexed in the vector database

---

## Appendix A — Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An AI-powered entity representing a country or international organization in the simulation |
| **Coordination Mode** | One of three settings controlling what inter-country communication and actions are available: No Coordination, Partial, Full |
| **Evidence Completeness** | A per-country float (0.0–1.0) representing how much of the crisis picture that country has access to at a given simulation time |
| **Information Delay** | The number of simulation minutes after T+0 before a given country becomes aware of the crisis |
| **Negotiation Round** | A phase in the simulation where the coordinator agent proposes a joint action and countries vote |
| **RAG** | Retrieval-Augmented Generation — the process of retrieving relevant governance document chunks and inserting them into an agent's prompt before LLM inference |
| **Risk Score** | A deterministic 0–100 score representing residual crisis risk; reduced by specific actions taken |
| **Simulation Tick** | One unit of simulation time (1 minute); the engine advances state on each tick |
| **T+N** | Shorthand for "N minutes after the crisis was first detected" |

---

## Appendix B — Metric Derivation Summary

| Metric | Source | Formula |
|--------|--------|---------|
| Risk Final | Simulation engine | `max(0, 100 + Σ action_reductions × (1 - 0.2 × coord_ratio))` |
| Risk Reduction % | Derived | `(100 - risk_final) / 100 × 100` |
| Response Time | Event timestamps | `coordinated_action_time - detection_time` (minutes) |
| Coordination Ratio | Vote tally | `countries_approving / countries_total` |
| Countries Coordinating | Vote tally | Count of countries with `approve` vote |
| Unresolved Issues | Negotiation log | Count of issues unresolved across > 1 negotiation round |

---

*PRD v1.0 — AI Governance Crisis Simulator — September 2026*

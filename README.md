# AI Governance Crisis Simulator

> **An interactive command-center simulation platform demonstrating how international AI governance strategies shape the outcome of cross-border AI crises.**
>
> *"The same crisis, governed differently, produces measurably different outcomes."*

---

## Executive Overview

The **AI Governance Crisis Simulator** is an empirical, multi-agent evaluation platform for international artificial intelligence policy. When critical frontier AI systems experience catastrophic cross-border failures, national governments must coordinate incident response under severe uncertainty, geopolitical friction, and asymmetric intelligence.

The simulator compares three distinct governance regimes on the exact same crisis scenario:
1. **Unilateral (No Coordination)**: Sovereign unilateral doctrine; independent state action with zero multilateral accord.
2. **Coalition (Partial Coordination)**: Bilateral/regional coalitions operating under 50% quorum and simple majority.
3. **Multilateral (Coordinated Governance)**: Inclusive multilateral treaty body operating under 60% quorum and qualified majority accord.

Outcomes are evaluated deterministically using a code-driven **4-Pillar Scoring Engine**:
- **Risk Reduction (%)**: Incident containment, spread prevention, and mitigation efficacy.
- **Response Timeliness (Minutes)**: Detection-to-action velocity across diplomatic channels.
- **Coordination Ratio**: Degree of multilateral consensus and collective treaty compliance.
- **Unresolved Policy Issues**: Critical liabilities, unaddressed contagion vectors, and diplomatic impasse points.

---

## System Architecture

```
                                 ┌────────────────────────┐
                                 │   Frontend Command     │
                                 │   Center (React/Vite)  │
                                 └───────────┬────────────┘
                                             │ REST / WebSocket
                                             ▼
                                 ┌────────────────────────┐
                                 │    FastAPI Backend     │
                                 │  (Port 8000, Python)   │
                                 └───────────┬────────────┘
                   ┌─────────────────────────┼─────────────────────────┐
                   ▼                         ▼                         ▼
        ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
        │ Simulation Clock & │    │ Country Agents &   │    │ Deterministic      │
        │ Event Queue Engine │    │ Coordinator (RAG)  │    │ Scoring (4 Pillars)│
        └──────────┬─────────┘    └──────────┬─────────┘    └──────────┬─────────┘
                   │                         │                         │
                   └─────────────────────────┼─────────────────────────┘
                                             ▼
                                 ┌────────────────────────┐
                                 │ Three-Mode Comparison  │
                                 │ & Authoritative Replay │
                                 └────────────────────────┘
```

---

## Key Capabilities

- **Deterministic Simulation Engine**: Discrete-tick event clock (`T+00`, `T+03`, `T+05`...) with asymmetric information delays and priority queues.
- **15 Fictional Nations**: Distinct national AI priorities, risk tolerances, decision speeds, and regulatory doctrines.
- **Multilateral Negotiation & Voting**: Multi-round diplomatic protocol with structured amendments, quorum validation, qualified majorities, and deadlock resolution.
- **RAG Governance Grounding**: Contextual retrieval from six core international governance frameworks (EU AI Act principles, OECD recommendations, US Executive Orders, NIST RMF, ISO/IEC 42001, G7 Hiroshima Process).
- **Three-Mode Comparison View**: Head-to-head empirical benchmarking of all three coordination modes on identical scenarios.
- **Seeded Demo & Authoritative Replay**: 100% reproducible offline presentation execution with timeline scrubbing, step-by-step playback, and speed controls.
- **Zero-Network Fallbacks**: Gracefully operates offline without external API keys or network dependencies.

---

## Quick Start

### 1. Requirements

| Component | Version | Description |
|---|---|---|
| **Python** | `>= 3.11` | Backend runtime & scientific libraries |
| **Node.js** | `>= 18` | Frontend toolchain & build pipeline |
| **npm** | `>= 9` | Frontend dependency manager |

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Linux / macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development API server
uvicorn app.main:app --port 8000 --reload
```

API Documentation (Swagger UI): `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development command center
npm run dev
```

Frontend Command Center: `http://localhost:5173`

---

## Presentation & Demo Walkthrough

### 1. Launching the Seeded Demo
1. Open `http://localhost:5173/demo` (or click **Demo & Replay Center** in the sidebar).
2. Confirm the **DEMO MODE** badge displays deterministic `Seed: 42` and `Deterministic Fallback: Active`.
3. Click **Run Seeded Demo (3 Modes)**.
4. Watch the simulator sequentially execute `uncoordinated`, `fragmented`, and `coordinated` modes through the authoritative simulation pipeline.
5. Review the **Authoritative Winner Banner**, 3-column breakdown cards, cross-mode metric comparison bars, and comparative pillar deltas.

### 2. Replay Scrubbing
1. Switch to the **2. Authoritative Replay** tab.
2. Use the timeline slider to scrub to any historical tick (`T+00` to `T+XX`).
3. Use **Step Forward** / **Step Back** buttons or toggle **Play / Pause** and playback speed (`1x`, `2x`, `4x`).
4. Replay displays authoritative recorded events without re-running LLMs or mutating source results.

---

## Testing & Quality Assurance

### Backend Automated Test Suite
```bash
cd backend
python -m pytest -v
# 162 passed across all 15 phases
```

### Frontend Automated Test Suite
```bash
cd frontend
npm test -- --run
# 69 passed across 13 test suites
```

### Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
# tsc -b && vite build (0 errors)
```

### Frontend Code Linter
```bash
cd frontend
npm run lint
# oxlint (0 warnings, 0 errors across 69 files)
```

---

## Phase Implementation Registry

| Phase | Milestone | Status |
|:---:|---|:---:|
| **01** | Repository Foundation & Stack Configuration | ✅ Completed |
| **02** | Static Governance, Country & Scenario Data Layer | ✅ Completed |
| **03** | Deterministic Event Engine & Simulation Clock | ✅ Completed |
| **04** | Country Agents & Structured Decision Providers | ✅ Completed |
| **05** | International Coordinator Agent & Treaty Synthesis | ✅ Completed |
| **06** | Multilateral Negotiation & Voting Protocols | ✅ Completed |
| **07** | Deterministic 4-Pillar Scoring Engine | ✅ Completed |
| **08** | REST API & Real-Time WebSocket Streaming | ✅ Completed |
| **09** | RAG Engine & Document Grounding | ✅ Completed |
| **10** | Command Center Shell & Frontend Client Layer | ✅ Completed |
| **11** | Interactive World Map & Real-Time Intelligence Feed | ✅ Completed |
| **12** | Governance Metrics Bar, Treaty Chamber & Timeline | ✅ Completed |
| **13** | Three-Mode Comparative Engine & Synthesis View | ✅ Completed |
| **14** | Presentation Demo Path, Seeded Replay & Fallbacks | ✅ Completed |
| **15** | Final Polish, Motion Accessibility & Complete QA | ✅ Completed |

---

## Safety & Non-Proliferation Boundary

The AI Governance Crisis Simulator is strictly a **civilian international policy and multilateral crisis governance simulation**. It models diplomatic coordination, early incident notification, evidence sharing, and safety protocols under fictional scenarios. It does not model tactical weapon systems, kinetic conflict, offensive cyber exploits, or operational military directives.

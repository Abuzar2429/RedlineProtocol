# Design — AI Governance Crisis Simulator

Covers dashboard UI/UX, visual language, and the narrative structure the design must support. For data schemas and backend structure, see `architecture.md`. For scoring/rule logic, see `rules.md`.

---

## 1. Design Goal

The dashboard must make an abstract governance simulation feel like a **live, watchable event** — not a static report. Every panel should update in near-real-time as the crisis timeline advances, so a judge or user can watch a crisis unfold from detection to resolution in under a minute.

Core narrative the UI must always be capable of telling:

> **Scenario → Crisis → Information asymmetry → AI agents → Negotiation → Decision → Quantitative outcome**

---

## 2. Dashboard Layout

Three-column layout with a persistent bottom metrics bar.

```
┌───────────────┬───────────────────────────┬───────────────────┐
│  CRISIS       │      WORLD / COUNTRY MAP   │  LIVE AI DECISIONS │
│  STATUS       │                            │                    │
│  (left)       │        (center)            │      (right)       │
├───────────────┴───────────────────────────┴───────────────────┤
│              LIVE METRICS (Response · Coordination ·           │
│              Risk ↓% · Unresolved Issues)                      │
├──────────────────────────────────────────────────────────────┤
│                  FINAL DECISION / JOINT AGREEMENT              │
└──────────────────────────────────────────────────────────────┘
```

### 2.1 Left Panel — Crisis Status

```
🚨 CRITICAL
AI SYSTEM INCIDENT

Severity
█████████░ 91%

Countries affected
15
```

- Severity shown as a progress/gauge bar, color-coded (green → yellow → red).
- Current simulation phase label (e.g., "Detection", "Negotiation", "Resolution") updates live.
- Countries-affected count is static per scenario; severity can shift as the crisis escalates.

### 2.2 Center Panel — World / Country Map

- Built with Leaflet or MapLibre.
- Each country rendered as a marker/dot, color-coded by current status:

```
🔴 Unaware
🟡 Investigating
🔵 Notified
🟢 Coordinating
```

- Markers transition color live as the event engine advances the timeline (Phase 2 of `phases.md`).
- Hovering/tapping a marker surfaces that country's current profile snippet and last known position.

### 2.3 Right Panel — Live AI Decisions Feed

- Streaming, reverse-chronological feed of agent outputs:

```
🇮🇳 Agent

Recommendation:
Share verified technical evidence.

Reason:
International coordination is likely
to reduce escalation risk.
```

- Each card shows: country flag/icon, recommended action, one-line rationale.
- When RAG is active (Phase 7), show a small citation chip (e.g., "Source: Incident Response Framework §3") so grounding is visible.
- New cards animate in as new LLM decisions resolve — this is the panel judges will watch most closely.

### 2.4 Bottom — Live Metrics Bar

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Response    │ Coordination│ Risk        │ Unresolved  │
│ 14 min      │ 11/15       │ ↓63%        │ 3           │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

- All four values are computed by the deterministic scoring engine (`rules.md`) — never displayed as raw LLM output.
- Values update live as the simulation progresses (e.g., response time starts blank/ticking until coordinated action occurs).

### 2.5 Final Decision Card

```
JOINT RESPONSE AGREEMENT

✓ Temporary containment
✓ Technical investigation
✓ International notification
✓ Evidence sharing
✓ Coordinated communication

11 countries approved
2 opposed
2 undecided
```

- Appears once negotiation concludes (Phase 4).
- Checklist style for approved actions; approval/opposition/undecided counts shown as a simple breakdown (numbers or a small stacked bar).

---

## 3. Comparative Runs View (Signature Demo Screen)

A dedicated screen/mode for the "same crisis, three governance conditions" demo (Phase 9 of `phases.md`).

- Side-by-side (or sequential animated bar-race) comparison of three runs:

| | No Coordination | Partial Coordination | Full Coordination |
|---|---|---|---|
| Response Time | 31 min | 21 min | 14 min |
| Coordination | 5/15 | 9/15 | 13/15 |
| Risk Reduction | 28% | 47% | 76% |

- Closing screen/message, large and centered:

> **"Governance strategy changed the outcome."**

This should be the last thing shown before Q&A — treat it as the pitch's climax slide, not a buried data table.

---

## 4. Visual & Interaction Language

- **Status color system** (consistent across map, cards, and metrics):
  - 🔴 Red = Unaware / high risk / opposed
  - 🟡 Yellow = Investigating / undecided / caution
  - 🔵 Blue = Notified / informational
  - 🟢 Green = Coordinating / approved / resolved
- **Motion:** favor small, purposeful animations (marker color transitions, card slide-ins, metric count-ups) over static refreshes — this is what sells "live simulation" versus "static report."
- **Typography/tone:** treat this as a serious operations/command-center interface (think crisis-response dashboards), not a playful consumer app — the subject matter (AI safety incidents) warrants a measured, credible visual tone.
- **Loading states:** every panel needs a distinct loading/skeleton state, since LLM calls introduce latency — never let a panel look broken or blank mid-generation.

---

## 5. Recommended Frontend Stack for This Design

| Need | Tool |
|---|---|
| Framework | React + TypeScript |
| Styling | Tailwind CSS |
| Charts/metrics | Recharts |
| Map | Leaflet or MapLibre |
| Live updates | WebSocket connection to FastAPI backend |

---

## 6. Design Checklist Before Demo

- [ ] Every panel has a loading state.
- [ ] Color coding is consistent across map, decision cards, and final agreement.
- [ ] Metrics bar values are traceable to the deterministic engine (`rules.md`), not the LLM.
- [ ] Comparative-runs screen is rehearsed as the closing beat of the pitch.
- [ ] A fallback recorded video exists in case live LLM calls lag during judging.

# AI Governance Crisis Simulator — Implementation Roadmap

A phased, hackathon-friendly build plan. No model training required — the simulation logic, structured data, and deterministic scoring *are* the innovation. An existing LLM is used only as a reasoning/negotiation engine on top of your system.

---

## 0. Guiding Principles

- **Don't train a model.** Use an existing LLM (via prompts + RAG) as the reasoning engine.
- **Determinism where it matters.** Risk reduction, response time, and coordination scores are calculated by your code, never hallucinated by the LLM.
- **The simulation is the product.** Country profiles, information asymmetry, timelines, and negotiation are the core innovation — not "a chatbot that talks about AI governance."
- **Ship a working demo early, then layer complexity.** Level 1 (prompt-based) → Level 2 (RAG) → Level 3 (fine-tuning, optional/future).

---

## Phase 1 — Foundations & Data Layer (Day 1, Morning)

**Goal:** Get the static data model in place before writing any simulation logic.

- [ ] Define project repo structure:
  ```
  /data
     /governance   (ai_principles.pdf, incident_response.pdf, ...)
     /countries    (country_a.json, country_b.json, ...)
     /scenarios    (crisis_001.json, crisis_002.json, ...)
  /backend
  /frontend
  ```
- [ ] Create **5–8 country profile JSON files** with fields:
  - `priorities`, `risk_tolerance`, `transparency`, `coordination`, `decision_speed`
- [ ] Create **2–3 crisis scenario YAML/JSON files** with:
  - `severity`, `affected_countries`, `initial_detection`, `information_delay` (per country), `potential_impacts`, `possible_actions`
- [ ] Define the **shared action list** (Do nothing, Investigate, Notify, Suspend, Request international investigation, Public warning, Share evidence, Impose restrictions).
- [ ] Choose tech stack: **React + TypeScript (frontend)**, **FastAPI + Python (backend)**, **PostgreSQL** (or SQLite for hackathon speed).

**Deliverable:** Static, hand-authored data files that fully describe one crisis end-to-end (even before any AI is wired in).

---

## Phase 2 — Crisis Event Engine (Day 1, Afternoon)

**Goal:** A deterministic timeline engine that drives the simulation clock, independent of the LLM.

- [ ] Build a **timeline/tick system** (`T+00`, `T+03`, `T+05`, ...) that advances simulation state.
- [ ] Implement **information asymmetry**: each country "unlocks" evidence/awareness based on its `information_delay`.
- [ ] Implement country status states: `Unaware → Investigating → Notified → Coordinating`.
- [ ] Emit events the frontend can subscribe to (WebSocket or polling): detection, notification, media report, emergency meeting trigger.
- [ ] Write this as pure backend logic first — test with hardcoded/mock decisions before adding the LLM.

**Deliverable:** Running a scenario produces a visible, timestamped sequence of state changes with no AI involved yet.

---

## Phase 3 — LLM-Driven Country Agents (Day 1 Evening / Day 2 Morning)

**Goal:** Give each country agent a "brain" using prompt engineering — Level 1 simulation.

- [ ] Design the **system prompt template** per agent:
  ```
  You are the AI advisor for {country}.
  Priorities: {priorities}
  Current crisis: {scenario_summary}
  Information completeness: {percent}
  Other countries' known positions: {summaries}
  Available actions: {action_list}
  Recommend the next action. Explain: (1) why, (2) risks, (3) expected international reaction.
  ```
- [ ] Call the LLM **once per agent per decision point**, not continuously — control cost/latency.
- [ ] Parse the LLM's response into a structured decision object (`{action, rationale, risk_note}`), using JSON-mode/structured output prompting.
- [ ] Wire agent decisions into the event engine so the timeline reflects real recommendations.

**Deliverable:** Each country agent produces a distinct, priority-driven recommendation during a live scenario run.

---

## Phase 4 — Negotiation & Coordination Logic (Day 2, Midday)

**Goal:** Agents don't just recommend in isolation — they negotiate toward (or away from) consensus.

- [ ] Add an **International Coordinator agent** that proposes a joint response by synthesizing all country positions.
- [ ] Implement a **voting/agreement structure**: each country agent evaluates the proposal and returns Approve / Reject / Undecided (+ rationale).
- [ ] Support multiple negotiation rounds if consensus isn't reached (cap at 2–3 rounds for demo pacing).
- [ ] Produce a final **Joint Response Agreement** object: approved actions, approval count, opposition, undecided, and unresolved issues (e.g., liability, data-sharing, attribution).

**Deliverable:** A negotiation transcript ending in either agreement, partial agreement, or breakdown — all inspectable/replayable.

---

## Phase 5 — Deterministic Scoring Engine (Day 2, Afternoon)

**Goal:** Convert simulation outcomes into hard numbers — this is what makes results defensible, not vibes-based.

- [ ] **Risk reduction score:** start at 100, subtract fixed weights per action taken:
  | Action | Risk Reduction |
  |---|---|
  | Early detection | -10 |
  | International alert | -15 |
  | System containment | -30 |
  | Evidence sharing | -10 |
  | Joint investigation | -15 |
  | Public warning | -5 |
- [ ] **Response time:** `coordinated_action_time - detection_time`, computed from the actual timeline, not asked of the LLM.
- [ ] **Coordination score:** `countries_agreed / countries_invited`.
- [ ] **Unresolved issues count:** extracted from negotiation rounds where no agreement was reached.
- [ ] Persist each run's metrics so scenarios can be compared later (Phase 7).

**Deliverable:** Every simulation run outputs a metrics object: `{response_time, coordination, risk_reduction, unresolved_issues}` computed purely by code.

---

## Phase 6 — Dashboard / Frontend (Day 2 Evening / Day 3 Morning)

**Goal:** Make the simulation *watchable* — this sells the demo.

- [ ] **Left panel — Crisis status:** severity meter, countries affected, live phase label.
- [ ] **Center panel — World/country map** (Leaflet or MapLibre) with color-coded status per country:
  - 🔴 Unaware · 🟡 Investigating · 🔵 Notified · 🟢 Coordinating
- [ ] **Right panel — Live AI decisions feed:** streaming agent recommendations with rationale, updating as the timeline advances.
- [ ] **Bottom metrics bar:** Response Time, Coordination (`x/15`), Risk ↓%, Unresolved Issues — using Recharts for any trend visuals.
- [ ] **Final agreement card:** checklist of approved actions + approval breakdown.
- [ ] Wire frontend to backend via WebSocket (preferred for live feel) or short-interval polling.

**Deliverable:** A running, click-to-start demo that visually narrates a crisis from detection to resolution.

---

## Phase 7 — RAG Layer for Governance Grounding (Day 3, Midday) — *Level 2*

**Goal:** Ground agent decisions in real governance documents instead of pure LLM improvisation.

- [ ] Collect a small corpus: AI governance principles, incident-reporting procedures, national AI regulations, international cooperation frameworks, cybersecurity incident-response frameworks.
- [ ] Chunk + embed documents into a vector store (e.g., pgvector, Chroma, or FAISS for hackathon speed).
- [ ] On each agent decision, retrieve top-k relevant chunks and inject them into the prompt before generation.
- [ ] Surface *which* governance document(s) influenced a decision in the UI (adds credibility to the demo).

**Deliverable:** Agent rationales now cite/reflect actual governance text, not just improvised reasoning.

---

## Phase 8 — Scenario Generator (Day 3, Afternoon) — Stretch Goal

**Goal:** Show the simulator generalizes beyond one hand-authored crisis.

- [ ] Build a randomizer for: severity, number of countries, information delay pattern, evidence quality, conflicting-priority injection (e.g., "one country refuses cooperation").
- [ ] Auto-generate 3–5 scenario variants for the live demo.
- [ ] Optionally batch-run many generated scenarios headlessly to produce a `crisis_training_dataset.jsonl` of `{scenario, decision, response_time, coordination, risk_reduction, unresolved_issues}` records — useful evaluation data, and a credible stepping stone toward future fine-tuning (not required for v1).

**Deliverable:** Proof that the engine handles novel crises, not just the one demo script.

---

## Phase 9 — The Signature Demo: Comparative Runs (Day 3, Late Afternoon)

**Goal:** The single most persuasive hackathon moment — same crisis, different governance conditions.

- [ ] Run the identical scenario three times under different coordination assumptions:
  - **No coordination:** ~31 min response, ~5/15 coordination, ~28% risk reduction
  - **Partial coordination:** ~21 min response, ~9/15 coordination, ~47% risk reduction
  - **Full coordinated governance:** ~14 min response, ~13/15 coordination, ~76% risk reduction
- [ ] Build a comparison view (side-by-side or animated bar race) showing the three outcomes.
- [ ] Close the demo on the thesis: **"Governance strategy changed the outcome."**

**Deliverable:** The closing slide/screen of your pitch.

---

## Phase 10 — Polish, Rehearse, Ship (Day 3, Evening)

- [ ] Add loading/empty states so the dashboard never looks broken mid-generation.
- [ ] Pre-record a fallback demo video in case live LLM calls are slow/rate-limited during judging.
- [ ] Write the pitch narrative: problem → simulation → live demo → comparative-run reveal → why it matters.
- [ ] Clean up README: setup instructions, architecture diagram, and "what we'd build next" (RAG expansion, fine-tuning on generated dataset, more countries/scenarios).

---

## Architecture Summary

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

## Suggested Timeline (Compressed 3-Day Hackathon)

| Day | Focus |
|---|---|
| Day 1 | Phases 1–3: Data layer, event engine, first working LLM agent |
| Day 2 | Phases 4–6: Negotiation, scoring, dashboard live |
| Day 3 | Phases 7–10: RAG, scenario generator (if time), comparative demo, polish |

## What NOT to Do (v1)

- Don't fine-tune a model — prompts + structured data get you further, faster.
- Don't let the LLM compute metrics — keep risk/response-time/coordination deterministic and code-driven.
- Don't over-invest in the scenario generator before the core single-scenario demo works end-to-end.

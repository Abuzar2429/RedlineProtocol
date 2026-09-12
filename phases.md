# Implementation Phases — AI Governance Crisis Simulator

A phased, hackathon-friendly build plan. Ship a working demo early (Level 1: prompt-based), then layer in RAG (Level 2) and stretch goals. See `architecture.md` for component details and `rules.md` for scoring formulas.

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
- [ ] Create **5–8 country profile JSON files** (priorities, risk_tolerance, transparency, coordination, decision_speed).
- [ ] Create **2–3 crisis scenario YAML/JSON files** (severity, affected_countries, initial_detection, information_delay, potential_impacts, possible_actions).
- [ ] Define the **shared action list** (Do nothing, Investigate, Notify, Suspend, Request international investigation, Public warning, Share evidence, Impose restrictions).
- [ ] Choose tech stack: React + TypeScript (frontend), FastAPI + Python (backend), PostgreSQL/SQLite.

**Deliverable:** Static, hand-authored data files that fully describe one crisis end-to-end, before any AI is wired in.

---

## Phase 2 — Crisis Event Engine (Day 1, Afternoon)

**Goal:** A deterministic timeline engine that drives the simulation clock, independent of the LLM.

- [ ] Build a tick system (`T+00`, `T+03`, `T+05`, ...) that advances simulation state.
- [ ] Implement information asymmetry: countries unlock evidence/awareness based on `information_delay`.
- [ ] Implement country status states: `Unaware → Investigating → Notified → Coordinating`.
- [ ] Emit events the frontend can subscribe to (WebSocket or polling): detection, notification, media report, emergency meeting trigger.
- [ ] Test with hardcoded/mock decisions before adding the LLM.

**Deliverable:** Running a scenario produces a visible, timestamped sequence of state changes with no AI involved yet.

---

## Phase 3 — LLM-Driven Country Agents (Day 1 Evening / Day 2 Morning)

**Goal:** Give each country agent a "brain" using prompt engineering — Level 1 simulation.

- [ ] Design the system prompt template per agent (see `architecture.md` §5).
- [ ] Call the LLM once per agent per decision point — not continuously — to control cost/latency.
- [ ] Parse each response into a structured decision object (`{action, rationale, risk_note}`) using JSON-mode/structured output prompting.
- [ ] Wire agent decisions into the event engine so the timeline reflects real recommendations.

**Deliverable:** Each country agent produces a distinct, priority-driven recommendation during a live scenario run.

---

## Phase 4 — Negotiation & Coordination Logic (Day 2, Midday)

**Goal:** Agents negotiate toward (or away from) consensus, not just recommend in isolation.

- [ ] Add an International Coordinator agent that proposes a joint response by synthesizing all country positions.
- [ ] Implement a voting structure: each country agent returns Approve / Reject / Undecided (+ rationale).
- [ ] Support multiple negotiation rounds if consensus isn't reached (cap at 2–3 rounds for demo pacing).
- [ ] Produce a final Joint Response Agreement object: approved actions, approval count, opposition, undecided, unresolved issues.

**Deliverable:** A negotiation transcript ending in agreement, partial agreement, or breakdown — inspectable/replayable.

---

## Phase 5 — Deterministic Scoring Engine (Day 2, Afternoon)

**Goal:** Convert outcomes into hard numbers, computed by code — see `rules.md` for exact formulas.

- [ ] Implement risk reduction scoring (weighted deductions per action).
- [ ] Implement response time calculation from the actual timeline.
- [ ] Implement coordination score (`agreed / invited`).
- [ ] Implement unresolved issues extraction from negotiation rounds.
- [ ] Persist each run's metrics for later comparison (Phase 9).

**Deliverable:** Every simulation run outputs `{response_time, coordination, risk_reduction, unresolved_issues}` computed purely by code.

---

## Phase 6 — Dashboard / Frontend (Day 2 Evening / Day 3 Morning)

**Goal:** Make the simulation watchable — this sells the demo. See `design.md` for full layout spec.

- [ ] Left panel — crisis status (severity meter, countries affected, phase label).
- [ ] Center panel — world/country map with color-coded status.
- [ ] Right panel — live AI decisions feed.
- [ ] Bottom metrics bar — Response Time, Coordination, Risk ↓%, Unresolved Issues.
- [ ] Final agreement card — approved actions + approval breakdown.
- [ ] Wire frontend to backend via WebSocket (preferred) or short-interval polling.

**Deliverable:** A running, click-to-start demo that visually narrates a crisis from detection to resolution.

---

## Phase 7 — RAG Layer for Governance Grounding (Day 3, Midday) — Level 2

**Goal:** Ground agent decisions in real governance documents instead of pure LLM improvisation.

- [ ] Collect a small corpus: AI governance principles, incident-reporting procedures, national AI regulations, international cooperation frameworks, cybersecurity incident-response frameworks.
- [ ] Chunk + embed documents into a vector store (pgvector, Chroma, or FAISS).
- [ ] On each agent decision, retrieve top-k relevant chunks and inject into the prompt before generation.
- [ ] Surface which governance document(s) influenced a decision in the UI.

**Deliverable:** Agent rationales reflect actual governance text, not just improvised reasoning.

---

## Phase 8 — Scenario Generator (Day 3, Afternoon) — Stretch Goal

**Goal:** Show the simulator generalizes beyond one hand-authored crisis.

- [ ] Build a randomizer for severity, country count, information delay pattern, evidence quality, conflicting-priority injection.
- [ ] Auto-generate 3–5 scenario variants for the live demo.
- [ ] Optionally batch-run generated scenarios headlessly to produce `crisis_training_dataset.jsonl` — useful evaluation data and a future fine-tuning stepping stone (not required for v1).

**Deliverable:** Proof that the engine handles novel crises, not just the one demo script.

---

## Phase 9 — The Signature Demo: Comparative Runs (Day 3, Late Afternoon)

**Goal:** The single most persuasive hackathon moment — same crisis, different governance conditions.

- [ ] Run the identical scenario three times under different coordination assumptions:
  - No coordination: ~31 min response, ~5/15 coordination, ~28% risk reduction
  - Partial coordination: ~21 min response, ~9/15 coordination, ~47% risk reduction
  - Full coordinated governance: ~14 min response, ~13/15 coordination, ~76% risk reduction
- [ ] Build a comparison view (side-by-side or animated bar race).
- [ ] Close the demo on the thesis: **"Governance strategy changed the outcome."**

**Deliverable:** The closing slide/screen of your pitch.

---

## Phase 10 — Polish, Rehearse, Ship (Day 3, Evening)

- [ ] Add loading/empty states so the dashboard never looks broken mid-generation.
- [ ] Pre-record a fallback demo video in case live LLM calls are slow/rate-limited during judging.
- [ ] Write the pitch narrative: problem → simulation → live demo → comparative-run reveal → why it matters.
- [ ] Clean up README: setup instructions, architecture diagram, and "what we'd build next."

---

## Suggested Timeline (Compressed 3-Day Hackathon)

| Day | Focus |
|---|---|
| Day 1 | Phases 1–3: Data layer, event engine, first working LLM agent |
| Day 2 | Phases 4–6: Negotiation, scoring, dashboard live |
| Day 3 | Phases 7–10: RAG, scenario generator (if time), comparative demo, polish |

## What NOT to Do (v1)

- Don't fine-tune a model — prompts + structured data get you further, faster.
- Don't let the LLM compute metrics — keep scoring deterministic and code-driven (see `rules.md`).
- Don't over-invest in the scenario generator before the core single-scenario demo works end-to-end.

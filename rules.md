# Rules — AI Governance Crisis Simulator

This document defines the **deterministic rules** governing the simulation: scoring formulas, agent decision inputs, negotiation mechanics, and governance-document grounding rules. The guiding principle throughout: **anything that can be computed by code must be computed by code — never left to LLM guesswork.**

---

## 1. Core Principle: Determinism Over Hallucination

> Don't ask the LLM "what was the risk reduction?" or "what was the response time?" — **calculate it.**

The LLM's role is restricted to:
- Generating a country's recommended action + rationale, given its profile and the current crisis state.
- Synthesizing/negotiating a joint proposal across countries.
- Identifying qualitative unresolved issues (e.g., "liability," "attribution") in negotiation transcripts.

The LLM's role explicitly **excludes**:
- Computing risk reduction percentages.
- Computing response time.
- Computing coordination ratios.
- Deciding scenario ground-truth facts (severity, information delay) — these are scenario-authored inputs, not model outputs.

---

## 2. Country Decision Inputs

Each country agent's decision is a function of:

```
Country priorities
+
Available information
+
Current risk
+
Governance rules (retrieved via RAG)
+
Previous actions (own and others')
```

Country profile fields that constrain/bias behavior:

| Field | Effect on behavior |
|---|---|
| `priorities` | Weights which actions an agent favors (e.g., "national_security" biases toward containment; "privacy"/"human_rights" biases toward transparency and caution) |
| `risk_tolerance` | Low tolerance → favors early/aggressive action; high tolerance → favors waiting for more evidence |
| `transparency` | High → favors evidence-sharing and public disclosure; low → favors internal investigation first |
| `coordination` | High → more likely to approve joint proposals; low → more likely to reject or delay |
| `decision_speed` | Fast → shorter internal deliberation before committing to a position; slow → more rounds before committing |

Available action set (shared across all countries, may be scenario-restricted):

```
1. Do nothing
2. Investigate internally
3. Notify affected countries
4. Suspend AI system
5. Request international investigation
6. Release public warning
7. Share technical evidence
8. Impose temporary restrictions
```

---

## 3. Information Asymmetry Rules

- Each country's visibility into the crisis is gated by its `information_delay` value (minutes) defined per-scenario.
- A country cannot act on evidence it has not yet "received" according to the timeline engine.
- Status progression per country is strictly sequential:

```
Unaware → Investigating → Notified → Coordinating
```

- A country cannot skip a state (e.g., cannot go straight from Unaware to Coordinating).

---

## 4. Negotiation & Voting Rules

- The International Coordinator agent proposes a joint response after a triggering event (e.g., emergency meeting reached, T+15 by default).
- Each country agent responds to a proposal with exactly one of: **Approve / Reject / Undecided**, plus a rationale.
- Negotiation proceeds in **rounds**, capped at **3 rounds** for demo pacing (configurable).
- A proposal is considered the **Final Joint Agreement** when either:
  - A round ends with no further changes to vote counts ("stable"), or
  - The maximum round count is reached.
- **Unresolved issues** are any concerns raised in Reject/Undecided rationales that are not addressed by a subsequent proposal revision (e.g., liability, data-sharing restrictions, attribution).

---

## 5. Scoring Formulas

### 5.1 Risk Reduction

Start every scenario at a baseline risk of 100. Each action taken by any country during the run applies a fixed deduction (deductions do not stack twice for the same action type in a single run, unless the scenario explicitly allows repeated application):

| Action | Risk Reduction |
|---|---|
| Early detection | -10 |
| International alert | -15 |
| System containment | -30 |
| Evidence sharing | -10 |
| Joint investigation | -15 |
| Public warning | -5 |

```
Example:
100 → 90 → 75 → 45 → 35 → 20

Final estimated risk: 20/100
Risk reduction: 80%
```

`risk_reduction_percent = (100 - final_risk) / 100 * 100`

### 5.2 Response Time

```python
response_time = coordinated_action_time - detection_time
```

```
Detection = 00:00
Coordinated response = 00:14
Response time = 14 minutes
```

Displayed as: `⏱️ Response Time: 14 min`

### 5.3 Coordination Score

```
coordination = countries_agreed / countries_invited
```

```
11 agreed / 15 invited = 73.3%
```

Displayed as: `🌐 Coordination: 11/15`

### 5.4 Unresolved Issues Count

A simple count of distinct unresolved concerns surfaced during negotiation (see §4). Displayed as a number (e.g., `3 unresolved issues`), optionally with labels:

```
⚠ Liability
⚠ Data-sharing restrictions
⚠ Attribution
```

---

## 6. Governance Document Grounding Rules (RAG)

- Governance documents (AI principles, incident-reporting procedures, national regulations, cooperation frameworks, cybersecurity response frameworks) are stored in a vector database, not memorized by the LLM.
- Before generating a decision, the system retrieves the top-k most relevant document chunks for the current country + crisis context and injects them into the prompt.
- Every agent decision that used retrieved context should record which document(s) informed it, so the rationale can be traced back to a source (surfaced in the UI per `design.md` §2.3).
- If no relevant governance document is retrieved for a decision, the agent falls back to profile-based reasoning alone — the UI should distinguish "grounded" from "ungrounded" recommendations.

---

## 7. Scenario Authoring Rules

- Every scenario must define, at minimum: `severity`, `affected_countries`, `initial_detection`, `information_delay` (per country), `potential_impacts`, `possible_actions`.
- `information_delay` values must be non-negative integers (minutes) and unique enough to create meaningful asymmetry (avoid all countries receiving information simultaneously, which trivializes the negotiation dynamic).
- Scenarios used for the **comparative demo** (see `phases.md` Phase 9) must be identical across runs except for the **coordination condition** being tested — changing more than one variable invalidates the comparison.

---

## 8. Scenario Generator Rules (Stretch Goal)

When randomly generating scenarios (`phases.md` Phase 8), the generator must respect the same schema and constraints as hand-authored scenarios (§7). Randomizable fields:

```
Severity
Information delay
Number of countries
Political priorities
Evidence quality
Infrastructure affected
Available actions
```

Generated scenarios feed into the same deterministic scoring engine (§5) — no special-casing for generated vs. hand-authored scenarios.

---

## 9. Guardrails Summary

- ✅ LLM generates: recommendations, rationales, negotiation positions, qualitative unresolved-issue framing.
- ✅ Code computes: risk reduction, response time, coordination score, final risk value.
- ❌ Never let the LLM report a numeric metric directly to the UI.
- ❌ Never let a country skip an information-state stage.
- ❌ Never compare governance strategies across scenarios that differ in more than the coordination condition being tested.

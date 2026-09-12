# Phase 7 — Deterministic Scoring Engine

## 1. Overview
The **Deterministic Scoring Engine** evaluates crisis response outcomes based strictly on authoritative simulation state and negotiation records. It operates purely on mathematical formulas and factual ledgers, ensuring 100% reproducibility, auditability, explainability, and total independence from LLM judgment.

Formula Version: `1.0`

---

## 2. Architecture & Data Flow

```
 authoritative SimulationState
                ↓
    ScoringSnapshotBuilder
                ↓
  immutable ScoringInputSnapshot
                ↓
    DeterministicScoringEngine
      ├── Metric 1: Risk Reduction
      ├── Metric 2: Response Time
      ├── Metric 3: Coordination Score
      └── Metric 4: Unresolved Issues
                ↓
   compute_overall_score (0–100, Grade A–F)
                ↓
          ScoringResult
     (Auditable & Replay-Safe)
```

---

## 3. The Four Deterministic Metrics

### Metric 1: Risk Reduction (`risk_reduction`)
- **Purpose**: Measures the percentage of crisis risk successfully mitigated through country policy interventions and multilateral coordination.
- **Formula**:
  $$\text{risk\_final} = \max\left(0, (100 + \sum \text{action\_deductions}) \times (1.0 - 0.2 \times \text{coordination\_ratio})\right)$$
  $$\text{risk\_reduction\_pct} = \frac{100 - \text{risk\_final}}{100} \times 100$$
- **Action Deductions** (deduplicated per action type):
  - `investigate_internally` / `early_detection`: -5 (-10 alias)
  - `notify_international` / `international_alert`: -15
  - `suspend_system_temporarily` / `system_containment`: -30
  - `share_technical_evidence` / `evidence_sharing`: -10
  - `request_joint_investigation` / `joint_investigation`: -15
  - `issue_public_warning` / `public_warning`: -5
  - `impose_temporary_restrictions`: -12
  - `bilateral_information_share`: -8
- **Normalization**: Normalized score = $\text{risk\_reduction\_pct} \in [0.0, 100.0]$.
- **Weight**: `0.25` (25%).

---

### Metric 2: Response Time (`response_time`)
- **Purpose**: Evaluates how swiftly the international community converged on a coordinated response using the virtual event clock (ticks in minutes).
- **Formula**:
  $$\text{response\_time} = \text{coordinated\_action\_time} - \text{detection\_time}$$
  - If coordinated response occurred:
    $$\text{normalized} = \max\left(0.0, \min\left(100.0, 100.0 - \left(\frac{\text{response\_time}}{\text{benchmark}}\right) \times 100.0\right)\right)$$
    where default $\text{benchmark} = 30\text{ minutes}$.
  - If uncoordinated (fallback to total crisis duration):
    $$\text{normalized} = \max\left(0.0, \min\left(30.0, 30.0 - \left(\frac{\text{response\_time}}{\text{benchmark}}\right) \times 15.0\right)\right)$$
- **Normalization**: Clamped to $[0.0, 100.0]$.
- **Weight**: `0.25` (25%).

---

### Metric 3: Coordination Score (`coordination`)
- **Purpose**: Quantifies multilateral consensus as the ratio of approving nations to total invited nations.
- **Formula**:
  $$\text{coordination\_ratio} = \frac{\text{approving\_countries}}{\text{total\_countries}}$$
- **Normalization**: $\text{coordination\_ratio} \times 100 \in [0.0, 100.0]$.
- **Weight**: `0.25` (25%).

---

### Metric 4: Unresolved Issues (`unresolved_issues`)
- **Purpose**: Penalizes lingering structural and diplomatic disagreements surfaced across negotiation rounds or cited in opposition votes.
- **Formula**:
  - Distinct count of unresolved issues surfaced in $>1$ round or cited in reject votes.
  - 0 issues = 100.0; each unresolved issue deducts 20.0 points:
    $$\text{normalized} = \max(0.0, \min(100.0, 100.0 - (\text{count} \times 20.0)))$$
- **Normalization**: Clamped to $[0.0, 100.0]$.
- **Weight**: `0.25` (25%).

---

## 4. Overall Composite Score & Grades

$$\text{overall\_score} = \sum_{i=1}^{4} (\text{normalized\_score}_i \times \text{weight}_i)$$

All weights are strictly equal:
$$\sum_{i=1}^4 \text{weight}_i = 0.25 + 0.25 + 0.25 + 0.25 = 1.00$$

### Grade Tiers
- **A** (85.0 – 100.0): Optimal Governance — Swift multilateral consensus decisively neutralized systemic crisis.
- **B** (70.0 – 84.9): Effective Multilateralism — Broad coalition achieved significant risk containment.
- **C** (50.0 – 69.9): Partial Containment — Interventions stabilized immediate danger but left friction.
- **D** (35.0 – 49.9): Fragmented Response — Coordination delays and dissent hindered comprehensive stability.
- **F** (0.0 – 34.9): Systemic Breakdown — Unilateral divergence failed to prevent critical escalation.

---

## 5. Rounding & Boundaries
- All raw values are processed with high floating-point precision.
- Clamping is applied explicitly at each normalization step to guarantee values stay strictly within $[0.0, 100.0]$.
- Final metric scores, weighted contributions, and overall composite scores are rounded to 2 decimal places.

---

## 6. Edge Cases Handled
- **Zero Events / Immediate Finish (T+0)**: Safely calculates risk at baseline (100.0), coordination ratio at 0.0, returning a valid structured score.
- **No Quorum / All Opposing or Abstaining**: Coordination ratio resolves to 0.0 with 0 divide-by-zero risk.
- **Unanimous Approval**: Clamps to 100.0 score, highest grade A.
- **Deduplication of Action Deductions**: Deductions do not stack twice for the same action type within a single run.
- **Max Negotiation Rounds / Deadlock**: Reflects unratified status and penalized unresolved issues.
- **Division by Zero Protection**: Guards on `total_countries <= 0` and `benchmark <= 0`.
- **Authoritative Ledgers Only**: Scoring engine queries only `SimulationState` or `ScoringInputSnapshot`.

---

## 7. REST API Endpoints

### 1. `POST /api/simulations/{id}/score`
Evaluates and persists the simulation's score.
- Optional query parameter: `require_completed: bool` (default `false`). If `true`, returns `400 Bad Request` if simulation has not reached `COMPLETED` status.
- Response: `ScoringResult` model.

### 2. `GET /api/simulations/{id}/score`
Retrieves the cached score or evaluates on-the-fly.
- Optional query parameter: `recalculate: bool` (default `false`).
- Response: `ScoringResult` model.

### 3. `GET /api/simulations/{id}/metrics`
Returns live `SimulationMetrics` for dashboard widgets during simulation runs.
- Response: `SimulationMetrics` object matching Spec §6.5.

### 4. `GET /api/simulations/{id}/score/breakdown`
Returns the array of 4 `MetricResult` objects with audit evidence.

"""
Deterministic Scoring Functions for AI Governance Crisis Simulator (Phase 7).

All metrics are pure mathematical functions:
- 100% deterministic & reproducible
- Zero LLM authority
- Explicit boundary clamping and division-by-zero protection
- Strict adherence to rules.md §5, spec.md §6, and PRD §7.5
"""
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.scoring_models import MetricId, MetricResult, ScoreGrade


# ── Constants ─────────────────────────────────────────────────────────────────

SCORING_FORMULA_VERSION = "1.0"
INITIAL_RISK = 100.0
DEFAULT_TOTAL_COUNTRIES = 15
BENCHMARK_RESPONSE_TICKS = 30.0

METRIC_WEIGHTS: Dict[MetricId, float] = {
    "risk_reduction": 0.25,
    "response_time": 0.25,
    "coordination": 0.25,
    "unresolved_issues": 0.25,
}

# Standard deduplication reduction values per action (spec §6.1 & rules.md §5.1)
DEFAULT_ACTION_RISK_REDUCTIONS: Dict[str, float] = {
    # Scenario Action IDs
    "investigate_internally": -5.0,
    "notify_international": -15.0,
    "notify_affected": -15.0,
    "suspend_system_temporarily": -30.0,
    "suspend_ai_system": -25.0,
    "share_technical_evidence": -10.0,
    "request_joint_investigation": -15.0,
    "request_multilateral_audit": -20.0,
    "issue_public_warning": -5.0,
    "impose_temporary_restrictions": -12.0,
    "bilateral_information_share": -8.0,
    "ratify_joint_containment": -35.0,
    # Canonical rule aliases (rules.md §5.1)
    "early_detection": -10.0,
    "international_alert": -15.0,
    "system_containment": -30.0,
    "evidence_sharing": -10.0,
    "joint_investigation": -15.0,
    "public_warning": -5.0,
}


# ── Pure Metric Functions ─────────────────────────────────────────────────────

def compute_risk_score(
    unique_actions: List[str],
    coordination_ratio: float,
    custom_reductions: Optional[Dict[str, float]] = None,
) -> Tuple[float, float, MetricResult]:
    """
    Computes Metric 1: Risk Final and Risk Reduction %.
    
    Formula (Spec §6.1 & Appendix A):
    risk_final = max(0.0, (INITIAL_RISK + sum(action_values)) * (1.0 - 0.2 * coordination_ratio))
    risk_reduction_pct = (INITIAL_RISK - risk_final) / INITIAL_RISK * 100.0
    
    Returns: (risk_final, risk_reduction_pct, MetricResult)
    """
    reductions_map = {**DEFAULT_ACTION_RISK_REDUCTIONS, **(custom_reductions or {})}
    
    # Deduplicate actions: fixed deductions do not stack twice for same action type
    deduped_actions = list(dict.fromkeys(unique_actions))
    
    applied_deductions: Dict[str, float] = {}
    sum_deductions = 0.0
    for action in deduped_actions:
        val = reductions_map.get(action, 0.0)
        applied_deductions[action] = val
        sum_deductions += val
        
    clamped_coord = max(0.0, min(1.0, float(coordination_ratio)))
    coord_multiplier = 1.0 - (0.2 * clamped_coord)
    
    risk_before_coord = max(0.0, INITIAL_RISK + sum_deductions)
    risk_final = max(0.0, min(100.0, risk_before_coord * coord_multiplier))
    risk_final = round(risk_final, 2)
    
    risk_reduction_pct = max(0.0, min(100.0, ((INITIAL_RISK - risk_final) / INITIAL_RISK) * 100.0))
    risk_reduction_pct = round(risk_reduction_pct, 2)
    
    normalized_score = risk_reduction_pct
    weight = METRIC_WEIGHTS["risk_reduction"]
    weighted_score = round(normalized_score * weight, 2)
    
    if risk_reduction_pct >= 70.0:
        interpretation = "High risk mitigation; systemic threat decisively neutralized."
    elif risk_reduction_pct >= 40.0:
        interpretation = "Moderate risk containment; collateral disruptions mitigated."
    else:
        interpretation = "Inadequate risk reduction; severe residual systemic exposure."
        
    result = MetricResult(
        metric_id="risk_reduction",
        name="Risk Reduction",
        raw_value=risk_reduction_pct,
        unit="%",
        display_value=f"↓{risk_reduction_pct:.0f}%",
        normalized_score=normalized_score,
        weight=weight,
        weighted_score=weighted_score,
        interpretation=interpretation,
        evidence={
            "initial_risk": INITIAL_RISK,
            "actions_evaluated": deduped_actions,
            "applied_deductions": applied_deductions,
            "total_deductions": sum_deductions,
            "risk_before_coordination": round(risk_before_coord, 2),
            "coordination_ratio": clamped_coord,
            "coordination_multiplier": round(coord_multiplier, 4),
            "risk_final": risk_final,
            "risk_reduction_pct": risk_reduction_pct,
        },
    )
    return risk_final, risk_reduction_pct, result


def compute_response_time(
    detection_tick: int,
    coordinated_action_tick: Optional[int],
    final_tick: int,
    benchmark_max_ticks: float = BENCHMARK_RESPONSE_TICKS,
) -> Tuple[int, MetricResult]:
    """
    Computes Metric 2: Response Time.
    
    Formula (Spec §6.2 & rules.md §5.2):
    response_time = coordinated_action_time - detection_time
    
    If no coordinated action occurred, falls back to total crisis duration (final_tick - detection_tick).
    
    Returns: (response_time_minutes, MetricResult)
    """
    det_tick = max(0, int(detection_tick))
    fin_tick = max(det_tick, int(final_tick))
    
    if coordinated_action_tick is not None and coordinated_action_tick >= det_tick:
        response_time_minutes = int(coordinated_action_tick - det_tick)
        coordinated_occurred = True
    else:
        response_time_minutes = int(fin_tick - det_tick)
        coordinated_occurred = False
        
    # Normalization: lower response time gives higher score
    benchmark = max(1.0, float(benchmark_max_ticks))
    if coordinated_occurred:
        norm = max(0.0, min(100.0, 100.0 - ((response_time_minutes / benchmark) * 100.0)))
    else:
        # Penalized for failure to coordinate
        norm = max(0.0, min(30.0, 30.0 - ((response_time_minutes / benchmark) * 15.0)))
        
    normalized_score = round(norm, 2)
    weight = METRIC_WEIGHTS["response_time"]
    weighted_score = round(normalized_score * weight, 2)
    
    if coordinated_occurred:
        display_value = f"{response_time_minutes} min"
        if response_time_minutes <= 15:
            interpretation = "Rapid diplomatic mobilization within critical golden window."
        elif response_time_minutes <= 25:
            interpretation = "Standard coordination latency; timely intervention achieved."
        else:
            interpretation = "Protracted deliberations; containment delayed."
    else:
        display_value = f"{response_time_minutes} min (uncoordinated)"
        interpretation = "No multilateral consensus reached during crisis timeline."
        
    result = MetricResult(
        metric_id="response_time",
        name="Response Time",
        raw_value=float(response_time_minutes),
        unit="minutes",
        display_value=display_value,
        normalized_score=normalized_score,
        weight=weight,
        weighted_score=weighted_score,
        interpretation=interpretation,
        evidence={
            "detection_tick": det_tick,
            "coordinated_action_tick": coordinated_action_tick,
            "final_tick": fin_tick,
            "coordinated_action_occurred": coordinated_occurred,
            "response_time_minutes": response_time_minutes,
            "benchmark_ticks": benchmark,
        },
    )
    return response_time_minutes, result


def compute_coordination_score(
    approving_count: int,
    total_countries: int = DEFAULT_TOTAL_COUNTRIES,
) -> Tuple[float, MetricResult]:
    """
    Computes Metric 3: Coordination Score / Ratio.
    
    Formula (Spec §6.3 & rules.md §5.3):
    coordination_ratio = approving_countries / total_countries (0.0 to 1.0)
    
    Returns: (coordination_ratio, MetricResult)
    """
    if total_countries <= 0:
        result = MetricResult(
            metric_id="coordination",
            name="Coordination Score",
            raw_value=0.0,
            unit="ratio",
            display_value="0/0",
            normalized_score=0.0,
            weight=METRIC_WEIGHTS["coordination"],
            weighted_score=0.0,
            interpretation="Zero coordination; no eligible participating countries.",
            evidence={
                "approving_countries": 0,
                "total_countries": 0,
                "coordination_ratio": 0.0,
                "percentage": 0.0,
            },
        )
        return 0.0, result

    total = int(total_countries)
    approving = max(0, min(total, int(approving_count)))
    
    coordination_ratio = round(approving / total, 4)
    normalized_score = round(coordination_ratio * 100.0, 2)
    weight = METRIC_WEIGHTS["coordination"]
    weighted_score = round(normalized_score * weight, 2)

    
    display_value = f"{approving}/{total}"
    if coordination_ratio >= 0.8:
        interpretation = "Overwhelming multilateral consensus with robust international legitimacy."
    elif coordination_ratio >= 0.5:
        interpretation = "Majority coalition established; viable international action ratified."
    elif coordination_ratio > 0.0:
        interpretation = "Fragmented bilateral alignment; failed to reach effective quorum."
    else:
        interpretation = "Zero coordination; isolated unilateral fragmentation."
        
    result = MetricResult(
        metric_id="coordination",
        name="Coordination Score",
        raw_value=coordination_ratio,
        unit="ratio",
        display_value=display_value,
        normalized_score=normalized_score,
        weight=weight,
        weighted_score=weighted_score,
        interpretation=interpretation,
        evidence={
            "approving_countries": approving,
            "total_countries": total,
            "coordination_ratio": coordination_ratio,
            "percentage": round(coordination_ratio * 100.0, 1),
        },
    )
    return coordination_ratio, result


def extract_and_score_unresolved_issues(
    unresolved_issues_raw: List[str],
    negotiation_rounds_count: int = 1,
    opposed_issues: Optional[List[str]] = None,
) -> Tuple[List[str], int, MetricResult]:
    """
    Computes Metric 4: Unresolved Issues Count & List.
    
    Formula (Spec §6.4 & rules.md §5.4):
    Extracted deterministically from negotiation records:
    - Issues that appeared in > 1 negotiation round without resolution
    - Issues that caused countries to vote oppose/reject
    
    Returns: (unresolved_issues_list, count, MetricResult)
    """
    opposed_set = set(opposed_issues or [])
    
    # Clean, normalize and deduplicate issue strings
    cleaned_issues: List[str] = []
    seen = set()
    for raw in unresolved_issues_raw:
        item = raw.strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            cleaned_issues.append(item)
            
    # Include any specific issues cited by opposing countries
    for raw in opposed_set:
        item = raw.strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            cleaned_issues.append(item)
            
    count = len(cleaned_issues)
    
    # Normalization: 0 issues = 100.0; each unresolved issue deducts 20 points
    norm = max(0.0, min(100.0, 100.0 - (count * 20.0)))
    normalized_score = round(norm, 2)
    weight = METRIC_WEIGHTS["unresolved_issues"]
    weighted_score = round(normalized_score * weight, 2)
    
    display_value = f"{count} unresolved" if count != 1 else "1 unresolved"
    if count == 0:
        interpretation = "Complete consensus; all strategic policy disputes resolved."
    elif count <= 2:
        interpretation = "Minor regulatory differences remain but operational agreement intact."
    elif count <= 4:
        interpretation = "Substantial diplomatic friction over sovereignty and compliance."
    else:
        interpretation = "Pervasive gridlock; severe structural disagreements unaddressed."
        
    result = MetricResult(
        metric_id="unresolved_issues",
        name="Unresolved Issues",
        raw_value=float(count),
        unit="count",
        display_value=display_value,
        normalized_score=normalized_score,
        weight=weight,
        weighted_score=weighted_score,
        interpretation=interpretation,
        evidence={
            "unresolved_count": count,
            "issues": cleaned_issues,
            "negotiation_rounds_evaluated": max(1, negotiation_rounds_count),
        },
    )
    return cleaned_issues, count, result


# ── Composite Overall Score & Grade ───────────────────────────────────────────

def compute_overall_score(
    metric_results: List[MetricResult],
) -> Tuple[float, ScoreGrade, str]:
    """
    Computes weighted overall composite score and letter grade.
    
    overall_score = sum(metric.weighted_score for metric in metric_results)
    
    Returns: (overall_score, grade, headline)
    """
    overall = sum(m.weighted_score for m in metric_results)
    overall_score = round(max(0.0, min(100.0, overall)), 2)
    
    if overall_score >= 85.0:
        grade: ScoreGrade = "A"
        headline = "Optimal Governance — Swift multilateral consensus decisively neutralized systemic crisis."
    elif overall_score >= 70.0:
        grade = "B"
        headline = "Effective Multilateralism — Broad coalition achieved significant risk containment."
    elif overall_score >= 50.0:
        grade = "C"
        headline = "Partial Containment — Interventions stabilized immediate danger but left friction."
    elif overall_score >= 35.0:
        grade = "D"
        headline = "Fragmented Response — Coordination delays and dissent hindered comprehensive stability."
    else:
        grade = "F"
        headline = "Systemic Breakdown — Unilateral divergence failed to prevent critical escalation."
        
    return overall_score, grade, headline

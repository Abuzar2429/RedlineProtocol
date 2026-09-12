"""
Deterministic Placeholder Decision Maker for Phase 3.

Evaluates available scenario actions against static country profiles
(priorities, risk tolerance, coordination willingness, transparency)
using rule-based evaluation without any LLM calls.
"""
import uuid
from typing import List, Optional

from app.schemas.data_models import CountryData, ScenarioAction
from app.schemas.simulation_models import CountrySimulationState, DecisionRecord


class DeterministicDecisionMaker:
    """
    Deterministic rule-based decision evaluator for country agents during Phase 3.
    """

    @classmethod
    def evaluate_decision(
        cls,
        simulation_id: str,
        country: CountryData,
        country_state: CountrySimulationState,
        available_actions: List[ScenarioAction],
        tick: int,
    ) -> DecisionRecord:
        """
        Selects the most aligned available action based on country characteristics.
        """
        if not available_actions:
            raise ValueError(f"No available actions provided for decision in country {country.id}")

        selected_action = cls._select_best_action(country, country_state, available_actions)
        reasoning, risks = cls._generate_deterministic_rationale(country, selected_action)

        decision_id = f"dec_{country.id}_{tick}_{uuid.uuid4().hex[:6]}"

        return DecisionRecord(
            decision_id=decision_id,
            simulation_id=simulation_id,
            country_id=country.id,
            tick=tick,
            action_id=selected_action.id,
            label=selected_action.label,
            reasoning=reasoning,
            risks_noted=risks,
            source="deterministic_placeholder",
            created_at_tick=tick,
        )

    @classmethod
    def _select_best_action(
        cls,
        country: CountryData,
        country_state: CountrySimulationState,
        actions: List[ScenarioAction],
    ) -> ScenarioAction:
        """
        Scores actions deterministically based on country traits.
        """
        scored_actions = []

        for action in actions:
            score = 0.0

            # 1. Coordination willingness preference
            if country.coordination_willingness == "high":
                score += action.coordination_effect * 30.0
            elif country.coordination_willingness == "low":
                score -= action.coordination_effect * 20.0

            # 2. Risk tolerance preference
            # Negative risk_reduction_value means risk decreases (e.g. -25 is high risk reduction)
            risk_reduction_magnitude = -action.risk_reduction_value
            if country.risk_tolerance == "low":
                score += risk_reduction_magnitude * 1.5
            elif country.risk_tolerance == "high":
                score += risk_reduction_magnitude * 0.5

            # 3. Transparency preference
            if country.transparency == "high" and action.visibility == "public":
                score += 15.0
            elif country.transparency == "low" and action.visibility == "private":
                score += 15.0

            # 4. Action requiring agreement
            if action.requires_agreement:
                if country.coordination_willingness == "high":
                    score += 10.0
                elif country.coordination_willingness == "low":
                    score -= 15.0

            # 5. Deterministic tie-breaker using lexical ID
            scored_actions.append((score, action.id, action))

        # Sort descending by score, ascending by action.id
        scored_actions.sort(key=lambda x: (x[0], -len(x[1])), reverse=True)
        return scored_actions[0][2]

    @classmethod
    def _generate_deterministic_rationale(
        cls,
        country: CountryData,
        action: ScenarioAction,
    ) -> tuple[str, str]:
        """
        Produces formatted justification and noted risks matching country doctrine.
        """
        coord = country.coordination_willingness
        risk = country.risk_tolerance
        priorities_str = ", ".join(country.strategic_priorities[:2])

        reasoning = (
            f"As {country.name} (Risk Tolerance: {risk}, Coordination: {coord}), "
            f"strategic alignment dictates choosing '{action.label}'. "
            f"This satisfies primary national priorities ({priorities_str}) "
            f"while maintaining proportional operational response."
        )

        risks_noted = (
            f"Potential operational exposure resulting from action '{action.id}'. "
            f"Risk reduction factor: {action.risk_reduction_value}, "
            f"multilateral coordination shift: {action.coordination_effect}."
        )

        return reasoning, risks_noted

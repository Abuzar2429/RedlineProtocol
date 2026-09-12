"""
Country Agent implementation with LLM reasoning, Pydantic validation, and deterministic fallback.
"""
import asyncio
import json
import logging
import re
import uuid
from typing import Optional

from app.agents.agent_models import CountryDecisionResponse, DecisionContext
from app.agents.agent_prompt import (
    COUNTRY_AGENT_PROMPT_VERSION,
    build_country_system_prompt,
    build_country_user_prompt,
)
from app.agents.context_builder import DecisionContextBuilder
from app.llm import LLMProvider, get_llm_provider
from app.schemas.data_models import CountryData, ScenarioData
from app.schemas.simulation_models import DecisionRecord, SimulationState
from app.services.simulation.decision_maker import DeterministicDecisionMaker

logger = logging.getLogger(__name__)


class CountryAgent:
    """
    Reusable Country Agent representing any of the 15 fictional nations.
    Produces structured, validated decisions using an LLM backend,
    with automatic deterministic fallback if the LLM is unavailable or fails.
    """

    def __init__(
        self,
        country: CountryData,
        provider: Optional[LLMProvider] = None,
        max_retries: int = 1,
    ):
        self.country = country
        self.provider = provider or get_llm_provider()
        self.max_retries = max_retries
        self.system_prompt = build_country_system_prompt(self.country)

    async def decide(
        self,
        state: SimulationState,
        scenario: ScenarioData,
        tick: int,
    ) -> DecisionRecord:
        """
        Executes the full agent decision pipeline:
        1. Builds filtered context respecting information boundaries.
        2. Generates prompt.
        3. Calls LLM provider with retry logic.
        4. Validates structured output schema and business constraints.
        5. Falls back to deterministic decision maker on any failure.
        """
        context = DecisionContextBuilder.build_context(
            country=self.country,
            state=state,
            scenario=scenario,
        )
        user_prompt = build_country_user_prompt(context)

        # Attempt LLM generation with bounded retries
        llm_result = None
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                llm_result = await self.provider.generate(
                    prompt=user_prompt,
                    system_prompt=self.system_prompt,
                )
                break
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "CountryAgent[%s] LLM call attempt %d failed: %s",
                    self.country.id,
                    attempt + 1,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(0.1)

        # If LLM invocation failed, trigger deterministic fallback
        if llm_result is None:
            logger.warning(
                "CountryAgent[%s] activating deterministic fallback due to LLM error: %s",
                self.country.id,
                last_error,
            )
            return self._execute_fallback(state, scenario, tick, reason=str(last_error))

        # Validate structured output
        validated_decision = self._parse_and_validate(llm_result.content, scenario)
        if validated_decision is None:
            logger.warning(
                "CountryAgent[%s] activating deterministic fallback due to invalid LLM output: %.120s...",
                self.country.id,
                llm_result.content,
            )
            return self._execute_fallback(
                state, scenario, tick, reason="LLM output schema/business validation failed"
            )

        # Resolve selected action's human-readable label
        matched_action = next(
            (a for a in scenario.available_actions if a.id == validated_decision.action_id),
            None,
        )
        label = matched_action.label if matched_action else validated_decision.action_id

        risks_str = "; ".join(validated_decision.risks) if validated_decision.risks else ""
        decision_id = f"dec_{self.country.id}_{tick}_{uuid.uuid4().hex[:6]}"

        return DecisionRecord(
            decision_id=decision_id,
            simulation_id=state.simulation_id,
            country_id=self.country.id,
            tick=tick,
            action_id=validated_decision.action_id,
            label=label,
            reasoning=validated_decision.reasoning,
            risks_noted=risks_str,
            source="llm_agent",
            created_at_tick=tick,
            provider=llm_result.provider,
            model=llm_result.model,
            latency_ms=llm_result.latency_ms,
            willingness_to_coordinate=validated_decision.willingness_to_coordinate,
            expected_reactions=validated_decision.expected_reactions,
            prompt_version=COUNTRY_AGENT_PROMPT_VERSION,
        )

    def _parse_and_validate(
        self,
        content: str,
        scenario: ScenarioData,
    ) -> Optional[CountryDecisionResponse]:
        """
        Parses JSON content and verifies Pydantic schema and business rules.
        """
        # Clean markdown fences if present
        clean_json = content.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\s*\n?", "", clean_json)
            clean_json = re.sub(r"\n?```\s*$", "", clean_json)

        try:
            raw_dict = json.loads(clean_json)
        except json.JSONDecodeError:
            # Try finding first { ... } block
            match = re.search(r"(\{.*\})", clean_json, re.DOTALL)
            if match:
                try:
                    raw_dict = json.loads(match.group(1))
                except json.JSONDecodeError:
                    return None
            else:
                return None

        try:
            decision_obj = CountryDecisionResponse.model_validate(raw_dict)
        except Exception as val_err:
            logger.debug("Pydantic validation failed for CountryAgent output: %s", val_err)
            return None

        # Business validation: action_id must be in scenario's available actions
        valid_action_ids = {a.id for a in scenario.available_actions}
        if decision_obj.action_id not in valid_action_ids:
            logger.warning(
                "CountryAgent output action_id '%s' is not in available actions: %s",
                decision_obj.action_id,
                valid_action_ids,
            )
            return None

        return decision_obj

    def _execute_fallback(
        self,
        state: SimulationState,
        scenario: ScenarioData,
        tick: int,
        reason: str = "",
    ) -> DecisionRecord:
        """
        Executes safe deterministic fallback and marks provenance as 'deterministic_fallback'.
        """
        country_state = state.countries.get(self.country.id)
        if not country_state:
            raise KeyError(f"Country state for {self.country.id} not found in simulation state")

        fallback_record = DeterministicDecisionMaker.evaluate_decision(
            simulation_id=state.simulation_id,
            country=self.country,
            country_state=country_state,
            available_actions=scenario.available_actions,
            tick=tick,
        )

        fallback_record.source = "deterministic_fallback"
        fallback_record.prompt_version = COUNTRY_AGENT_PROMPT_VERSION
        if reason:
            fallback_record.risks_noted = f"[Fallback triggered: {reason[:80]}] {fallback_record.risks_noted}".strip()

        return fallback_record

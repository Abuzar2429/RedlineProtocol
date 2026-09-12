"""
International Coordinator Agent implementation (Phase 5).
Synthesizes country positions, invokes LLM with temperature 0.3,
validates proposals, and provides a deterministic fallback.
"""
import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional

from app.agents.coordinator_context_builder import CoordinatorContextBuilder
from app.agents.coordinator_models import (
    CoordinatorContext,
    CoordinatorProposal,
    PredictedVotes,
)
from app.agents.coordinator_prompt import (
    COORDINATOR_PROMPT_VERSION,
    build_coordinator_system_prompt,
    build_coordinator_user_prompt,
)
from app.config.settings import settings
from app.llm import LLMProvider, get_llm_provider
from app.schemas.simulation_models import SimulationEvent, SimulationState

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Dedicated AI International Coordinator Agent.
    Synthesizes validated country positions into a proposed multilateral response.
    Does NOT modify simulation state, does NOT self-approve proposals.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        max_retries: int = 1,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self.provider = provider or get_llm_provider()
        self.max_retries = max_retries
        self.model = model or getattr(settings, "COORDINATOR_MODEL", settings.LLM_MODEL)
        self.temperature = temperature if temperature is not None else getattr(settings, "COORDINATOR_TEMPERATURE", 0.3)
        self.system_prompt = build_coordinator_system_prompt()

    async def propose(
        self,
        state: SimulationState,
        current_event: Optional[SimulationEvent] = None,
        round_index: int = 1,
        country_catalog: Optional[Dict[str, Any]] = None,
    ) -> CoordinatorProposal:
        """
        Synthesizes validated positions and generates a proposal.
        Executes deterministic fallback on any LLM or validation failure.
        """
        # 1. Build context respecting strict information boundary
        context = CoordinatorContextBuilder.build_context(
            state=state,
            current_event=current_event,
            country_catalog=country_catalog,
        )
        user_prompt = build_coordinator_user_prompt(context)

        # 2. Invoke LLM with retry
        llm_result = None
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                llm_result = await self.provider.generate(
                    prompt=user_prompt,
                    system_prompt=self.system_prompt,
                    temperature=self.temperature,
                )
                break
            except Exception as exc:
                last_error = exc
                logger.warning("CoordinatorAgent LLM call attempt %d failed: %s", attempt + 1, exc)
                if attempt < self.max_retries:
                    await asyncio.sleep(0.1)

        # 3. Check for LLM generation failure -> fallback
        if llm_result is None:
            logger.warning("CoordinatorAgent triggering deterministic fallback due to LLM failure: %s", last_error)
            return self._execute_fallback(
                state=state,
                context=context,
                current_event=current_event,
                round_index=round_index,
                reason=str(last_error),
            )

        # 4. Parse and business-validate output
        validated_proposal = self._parse_and_validate(
            content=llm_result.content,
            state=state,
            current_event=current_event,
            round_index=round_index,
            llm_result=llm_result,
        )

        if validated_proposal is None:
            logger.warning(
                "CoordinatorAgent triggering deterministic fallback due to invalid LLM output: %.120s...",
                llm_result.content,
            )
            return self._execute_fallback(
                state=state,
                context=context,
                current_event=current_event,
                round_index=round_index,
                reason="LLM proposal schema or business validation failed",
            )

        return validated_proposal

    def _parse_and_validate(
        self,
        content: str,
        state: SimulationState,
        current_event: Optional[SimulationEvent],
        round_index: int,
        llm_result: Any,
    ) -> Optional[CoordinatorProposal]:
        """
        Parses JSON response, validates against Pydantic schema and business rules.
        """
        clean_json = content.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\s*\n?", "", clean_json)
            clean_json = re.sub(r"\n?```\s*$", "", clean_json)

        try:
            raw_dict = json.loads(clean_json)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\})", clean_json, re.DOTALL)
            if match:
                try:
                    raw_dict = json.loads(match.group(1))
                except json.JSONDecodeError:
                    return None
            else:
                return None

        if not isinstance(raw_dict, dict):
            return None

        # Extract proposal items and rationale if nested under "proposal"
        if "proposal" in raw_dict and isinstance(raw_dict["proposal"], dict):
            nested = raw_dict["proposal"]
            if "items" in nested and "items" not in raw_dict:
                raw_dict["items"] = nested["items"]
            if "rationale" in nested and "rationale" not in raw_dict:
                raw_dict["rationale"] = nested["rationale"]
            if "title" in nested and "title" not in raw_dict:
                raw_dict["title"] = nested["title"]
            if "summary" in nested and "summary" not in raw_dict:
                raw_dict["summary"] = nested["summary"]

        # Ensure required top-level defaults if omitted
        raw_dict.setdefault("title", f"Multilateral Action Framework - Round {round_index}")
        raw_dict.setdefault("summary", raw_dict.get("rationale", "Proposed joint crisis response framework."))
        raw_dict.setdefault("items", ["Establish verified bilateral/multilateral communication channel"])
        raw_dict.setdefault("rationale", "Promotes coordination while mitigating escalation risks.")
        raw_dict.setdefault("proposal_type", "JOINT_RESPONSE")
        raw_dict.setdefault("confidence", 0.80)

        # Structure predicted_votes
        if "predicted_votes" in raw_dict and isinstance(raw_dict["predicted_votes"], dict):
            pv = raw_dict["predicted_votes"]
            pv.setdefault("approve", [])
            pv.setdefault("oppose", [])
            pv.setdefault("abstain", [])
        else:
            raw_dict["predicted_votes"] = {"approve": [], "oppose": [], "abstain": []}

        # Business validation: referenced countries must exist in simulation
        valid_country_ids = set(state.countries.keys())
        pv = raw_dict["predicted_votes"]
        for group_name in ["approve", "oppose", "abstain"]:
            pv[group_name] = [c for c in pv.get(group_name, []) if c in valid_country_ids]

        raw_dict["supporting_countries"] = [
            c for c in raw_dict.get("supporting_countries", pv.get("approve", []))
            if c in valid_country_ids
        ]
        raw_dict["opposing_countries"] = [
            c for c in raw_dict.get("opposing_countries", pv.get("oppose", []))
            if c in valid_country_ids
        ]

        # Generate proposal ID with provenance
        event_id = current_event.event_id if current_event else f"tick_{state.current_tick}"
        proposal_id = f"prop_{round_index:03d}_{state.simulation_id[:8]}_t{state.current_tick:02d}"

        try:
            proposal = CoordinatorProposal(
                proposal_id=proposal_id,
                simulation_id=state.simulation_id,
                event_id=event_id,
                tick=state.current_tick,
                round=round_index,
                proposal_type=raw_dict.get("proposal_type", "JOINT_RESPONSE"),
                title=raw_dict.get("title", f"Proposal Round {round_index}"),
                summary=raw_dict.get("summary", ""),
                items=raw_dict.get("items", []),
                rationale=raw_dict.get("rationale", ""),
                predicted_votes=PredictedVotes(**raw_dict["predicted_votes"]),
                unresolved_issues=raw_dict.get("unresolved_issues", []),
                supporting_countries=raw_dict["supporting_countries"],
                opposing_countries=raw_dict["opposing_countries"],
                confidence=float(raw_dict.get("confidence", 0.80)),
                source="llm_coordinator",
                status="PROPOSED",
                model=getattr(llm_result, "model", self.model),
                provider=getattr(llm_result, "provider", "llm"),
                latency_ms=getattr(llm_result, "latency_ms", 0.0),
                prompt_version=COORDINATOR_PROMPT_VERSION,
            )
            return proposal
        except Exception as err:
            logger.debug("CoordinatorProposal Pydantic validation error: %s", err)
            return None

    def _execute_fallback(
        self,
        state: SimulationState,
        context: CoordinatorContext,
        current_event: Optional[SimulationEvent],
        round_index: int,
        reason: str = "",
    ) -> CoordinatorProposal:
        """
        Generates a 100% deterministic, reproducible proposal based on actual validated positions.
        """
        event_id = current_event.event_id if current_event else f"tick_{state.current_tick}"
        proposal_id = f"prop_{round_index:03d}_{state.simulation_id[:8]}_t{state.current_tick:02d}"

        # Deterministic sorting of countries based on willingness
        approving: list[str] = []
        opposing: list[str] = []
        abstaining: list[str] = []
        collected_risks: list[str] = []

        for p in context.participating_countries:
            if p.risks_noted:
                collected_risks.extend(p.risks_noted)
            if p.status == "Unaware":
                abstaining.append(p.country_id)
            elif p.willingness_to_coordinate >= 0.50:
                approving.append(p.country_id)
            elif p.willingness_to_coordinate < 0.35:
                opposing.append(p.country_id)
            else:
                abstaining.append(p.country_id)

        # Formulate items based on common ground and majority action
        majority = context.aggregation.majority_action or "share_telemetry"
        items = [
            f"Establish immediate secure diplomatic data-sharing channel regarding '{majority}'.",
            "Mandate joint technical verification of critical model telemetry within 24 hours.",
            "Enact mutual restraint on unilateral retaliatory countermeasures during active investigation.",
        ]

        # Common unresolved issues
        unresolved = [
            "Verification authority and jurisdiction over sovereign model checkpoints.",
            "Balancing proprietary safety boundaries with mandatory multilateral disclosure.",
        ]
        if collected_risks:
            # Pick first unique risk as concrete contested issue
            unique_risks = list(dict.fromkeys(collected_risks))
            if unique_risks:
                unresolved.append(f"Operational risk concern: {unique_risks[0][:90]}")

        rationale = (
            f"Deterministic synthesis based on {context.aggregation.aware_countries}/{context.aggregation.total_countries} "
            f"aware nations. Prioritizes transparency and mutual verification around '{majority}' to halt escalation."
        )
        if reason:
            rationale += f" [Synthesis Fallback Mode: {reason[:60]}]"

        return CoordinatorProposal(
            proposal_id=proposal_id,
            simulation_id=state.simulation_id,
            event_id=event_id,
            tick=state.current_tick,
            round=round_index,
            proposal_type="JOINT_RESPONSE",
            title=f"Joint Crisis Stabilization Framework (Round {round_index})",
            summary=f"Immediate multilateral verification and data-sharing accord addressing {state.crisis_state.title}.",
            items=items,
            rationale=rationale,
            predicted_votes=PredictedVotes(
                approve=sorted(approving),
                oppose=sorted(opposing),
                abstain=sorted(abstaining),
            ),
            unresolved_issues=unresolved,
            supporting_countries=sorted(approving),
            opposing_countries=sorted(opposing),
            confidence=0.75,
            source="deterministic_fallback",
            status="PROPOSED",
            model="deterministic-synthesizer",
            provider="code",
            latency_ms=0.5,
            prompt_version=COORDINATOR_PROMPT_VERSION,
        )

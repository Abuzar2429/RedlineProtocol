"""
Deterministic Mock LLM Provider for zero-credential testing and development.
"""
import asyncio
import json
import re
import time
from typing import Any, Dict, Optional

from app.llm.provider import LLMProvider, LLMResult


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider that simulates LLM reasoning without calling external APIs.
    """

    def __init__(
        self,
        model: str = "mock-governance-model",
        simulate_error: bool = False,
        simulate_timeout: bool = False,
        simulate_malformed: bool = False,
    ):
        self.model = model
        self.simulate_error = simulate_error
        self.simulate_timeout = simulate_timeout
        self.simulate_malformed = simulate_malformed
        self.invocation_count = 0

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> LLMResult:
        self.invocation_count += 1
        start_time = time.perf_counter()

        if self.simulate_timeout:
            raise asyncio.TimeoutError("Mock provider simulated timeout")

        if self.simulate_error:
            raise RuntimeError("Mock provider simulated upstream API error (503 Service Unavailable)")

        if self.simulate_malformed:
            return LLMResult(
                content="This is not valid JSON string at all {{{",
                provider="mock",
                model=self.model,
                latency_ms=1.5,
                parsed_json=None,
            )

        # Check if this is an International Coordinator invocation
        if "international coordinator" in system_prompt.lower() or "coordination task" in prompt.lower():
            # Extract participating country IDs from the prompt
            country_ids = re.findall(r"- Country:\s*[^\n\(]+\(([a-zA-Z0-9_-]+)\)", prompt)
            if not country_ids:
                country_ids = re.findall(r"country_[0-9]{2}", prompt)
            if not country_ids:
                country_ids = ["country_01", "country_02", "country_03", "country_04"]

            # Sort deterministically
            unique_countries = list(dict.fromkeys(country_ids))
            half = max(1, len(unique_countries) // 2)
            approving = unique_countries[:half]
            opposing = unique_countries[half:half + 1] if len(unique_countries) > half else []
            abstaining = unique_countries[half + 1:] if len(unique_countries) > half + 1 else []

            data = {
                "proposal_type": "JOINT_RESPONSE",
                "title": "International AI Incident Containment Protocol",
                "summary": "Coordinated multilateral protocol establishing joint technical verification and telemetry sharing.",
                "items": [
                    "Establish emergency cryptographic hotline for real-time model telemetry disclosure.",
                    "Authorize neutral international safety inspection team for affected deployment clusters.",
                    "Commit to temporary moratoria on retaliatory asymmetric cyber or regulatory counter-measures.",
                ],
                "rationale": "Balances urgent systemic containment against sovereign national security constraints.",
                "predicted_votes": {
                    "approve": approving,
                    "oppose": opposing,
                    "abstain": abstaining,
                },
                "unresolved_issues": [
                    "Inspection protocol access boundaries and proprietary source code protection.",
                    "Enforcement mechanisms for non-compliant algorithmic deployments.",
                ],
                "supporting_countries": approving,
                "opposing_countries": opposing,
                "confidence": 0.85,
            }

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return LLMResult(
                content=json.dumps(data, indent=2),
                provider="mock",
                model=self.model,
                latency_ms=max(1.0, latency_ms),
                parsed_json=data,
                prompt_tokens=220,
                completion_tokens=140,
            )

        # Extract country name and available action IDs from the prompt
        country_match = re.search(r"Country:\s*([^\n\r]+)", prompt)
        country_name = country_match.group(1).strip() if country_match else "Sovereign State"

        # Extract available action IDs mentioned in the prompt
        action_matches = re.findall(r"- ID:\s*([a-zA-Z0-9_-]+)", prompt)
        if not action_matches:
            action_matches = ["investigate_internally", "notify_affected", "do_nothing"]

        # Deterministically select action based on country characteristics in prompt
        selected_action = action_matches[0]
        if "privacy" in prompt.lower() or "regulation" in prompt.lower():
            for act in action_matches:
                if any(k in act for k in ["audit", "suspend", "restrictions", "investigate"]):
                    selected_action = act
                    break
        elif "coordination" in prompt.lower() or "international" in prompt.lower():
            for act in action_matches:
                if any(k in act for k in ["joint", "notify", "share", "audit"]):
                    selected_action = act
                    break

        willingness = 0.85 if "high" in prompt.lower() else 0.50

        data = {
            "action_id": selected_action,
            "reasoning": (
                f"As the designated policy authority for {country_name}, national strategic doctrine "
                f"mandates selecting action '{selected_action}' to mitigate cross-border exposure while "
                f"safeguarding sovereign operational capabilities."
            ),
            "risks": [
                f"Potential delay in regional synchronization caused by '{selected_action}'.",
                "Diplomatic pushback from non-participating neighboring states.",
            ],
            "expected_reactions": "Allied states expected to support; rival blocs may withhold data.",
            "willingness_to_coordinate": willingness,
        }

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return LLMResult(
            content=json.dumps(data, indent=2),
            provider="mock",
            model=self.model,
            latency_ms=max(1.0, latency_ms),
            parsed_json=data,
            prompt_tokens=150,
            completion_tokens=90,
        )

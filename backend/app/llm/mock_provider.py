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

"""
LLM Provider Abstraction for AI Governance Crisis Simulator.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMResult:
    """
    Standardized result payload from any LLM provider invocation.
    """
    content: str
    provider: str
    model: str
    latency_ms: float
    parsed_json: Optional[Dict[str, Any]] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class LLMProvider(ABC):
    """
    Abstract interface for LLM backends.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> LLMResult:
        """
        Submits prompt and returns structured LLMResult.
        Raises an exception if the provider call fails.
        """
        pass

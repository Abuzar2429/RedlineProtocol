"""
LLM abstraction package for AI Governance Crisis Simulator.
"""
from typing import Optional

from app.config.settings import Settings, settings as default_settings
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.provider import LLMProvider, LLMResult

__all__ = [
    "LLMProvider",
    "LLMResult",
    "MockLLMProvider",
    "AnthropicProvider",
    "get_llm_provider",
]


def get_llm_provider(settings: Optional[Settings] = None) -> LLMProvider:
    """
    Factory resolving configured LLMProvider based on application settings.
    """
    cfg = settings or default_settings
    provider_name = cfg.LLM_PROVIDER.strip().lower()

    if provider_name == "mock":
        return MockLLMProvider(model=cfg.LLM_MODEL)

    if provider_name == "anthropic":
        api_key = cfg.LLM_API_KEY or cfg.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError(
                "LLM_PROVIDER is set to 'anthropic' but no API key was found. "
                "Please configure ANTHROPIC_API_KEY or LLM_API_KEY in .env, "
                "or set LLM_PROVIDER=mock for offline simulation."
            )
        return AnthropicProvider(
            api_key=api_key,
            model=cfg.LLM_MODEL,
            default_timeout=cfg.LLM_TIMEOUT,
        )

    # Fallback to mock with warning
    return MockLLMProvider(model=f"mock-{provider_name}")

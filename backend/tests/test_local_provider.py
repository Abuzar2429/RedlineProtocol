"""
Unit tests for Local and Ollama LLM Providers (Phase 3).
"""
import json
import pytest
import httpx
from app.config.settings import Settings
from app.llm import get_llm_provider, OllamaProvider, LocalOpenAICompatibleProvider, MockLLMProvider
from app.llm.provider import LLMResult


@pytest.mark.asyncio
async def test_ollama_provider_success():
    """
    Tests successful generation and JSON parsing with OllamaProvider.
    """
    mock_response = {
        "model": "redline-llm",
        "message": {
            "role": "assistant",
            "content": json.dumps({
                "action_id": "ratify_joint_containment",
                "reasoning": "Sovereign alignment favors coordinated containment.",
                "risks": ["Telemetry leakage"],
                "expected_reactions": "Allies approve.",
                "willingness_to_coordinate": 0.85
            })
        },
        "prompt_eval_count": 128,
        "eval_count": 64
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        body = json.loads(request.read())
        assert body["model"] == "redline-llm"
        assert body["format"] == "json"
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    provider = OllamaProvider(base_url="http://mock-ollama:11434", model="redline-llm")

    # Patch AsyncClient to use transport
    original_client_init = httpx.AsyncClient.__init__

    def mock_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        original_client_init(self, *args, **kwargs)

    httpx.AsyncClient.__init__ = mock_init
    try:
        result = await provider.generate(
            prompt="Respond in JSON with action_id and reasoning",
            system_prompt="You are a crisis delegate.",
            temperature=0.3
        )
    finally:
        httpx.AsyncClient.__init__ = original_client_init

    assert isinstance(result, LLMResult)
    assert result.provider == "ollama"
    assert result.parsed_json is not None
    assert result.parsed_json["action_id"] == "ratify_joint_containment"
    assert result.prompt_tokens == 128
    assert result.completion_tokens == 64


@pytest.mark.asyncio
async def test_local_openai_compatible_provider_success():
    """
    Tests OpenAI-compatible local provider (vLLM / LM Studio / LocalAI).
    """
    mock_response = {
        "model": "redline-llm-vllm",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "proposal_type": "JOINT_RESPONSE",
                        "title": "Emergency Containment Accord",
                        "summary": "Coordinated de-escalation protocol",
                        "confidence": 0.90
                    })
                }
            }
        ],
        "usage": {
            "prompt_tokens": 256,
            "completion_tokens": 128
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers.get("authorization") == "Bearer test-key"
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    provider = LocalOpenAICompatibleProvider(
        base_url="http://mock-local:8000/v1",
        model="redline-llm-vllm",
        api_key="test-key"
    )

    original_client_init = httpx.AsyncClient.__init__

    def mock_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        original_client_init(self, *args, **kwargs)

    httpx.AsyncClient.__init__ = mock_init
    try:
        result = await provider.generate(
            prompt="Synthesize multilateral consensus in JSON",
            system_prompt="You are the International Coordinator.",
            temperature=0.3
        )
    finally:
        httpx.AsyncClient.__init__ = original_client_init

    assert isinstance(result, LLMResult)
    assert result.provider == "local"
    assert result.parsed_json is not None
    assert result.parsed_json["proposal_type"] == "JOINT_RESPONSE"
    assert result.prompt_tokens == 256
    assert result.completion_tokens == 128


def test_factory_resolution():
    """
    Tests that get_llm_provider correctly resolves providers according to settings.
    """
    settings_ollama = Settings(LLM_PROVIDER="ollama", LLM_MODEL="redline-llm")
    p_ollama = get_llm_provider(settings_ollama)
    assert isinstance(p_ollama, OllamaProvider)
    assert p_ollama.model == "redline-llm"

    settings_local = Settings(LLM_PROVIDER="local", LLM_MODEL="redline-llm-vllm")
    p_local = get_llm_provider(settings_local)
    assert isinstance(p_local, LocalOpenAICompatibleProvider)

    settings_mock = Settings(LLM_PROVIDER="mock")
    p_mock = get_llm_provider(settings_mock)
    assert isinstance(p_mock, MockLLMProvider)

"""
Local and Self-Hosted LLM Provider implementations (Phase 3).
Supports Ollama, vLLM, LM Studio, and OpenAI-compatible inference servers.
"""
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

from app.llm.provider import LLMProvider, LLMResult

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Direct asynchronous client for self-hosted Ollama instances.
    Runs fine-tuned Redline-LLM or open-source foundation models locally.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "redline-llm",
        default_timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.default_timeout = default_timeout

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> LLMResult:
        start_time = time.perf_counter()
        req_timeout = timeout or self.default_timeout

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else 0.3,
            },
        }

        # Check if the prompt requests JSON
        if "json" in prompt.lower() or "json" in system_prompt.lower():
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=req_timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
            except httpx.ConnectError as e:
                raise ConnectionError(
                    f"Failed to connect to Ollama at {self.base_url}. "
                    "Ensure Ollama is running (`ollama serve`). Error: " + str(e)
                ) from e
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Ollama request timed out after {req_timeout}s: {e}") from e

            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama returned HTTP error {response.status_code}: {response.text}"
                )

            data = response.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        message = data.get("message", {})
        content_text = message.get("content", "").strip()

        parsed_json = None
        try:
            parsed_json = json.loads(content_text)
        except json.JSONDecodeError:
            # Try to extract JSON between code fences or brackets
            if "{" in content_text and "}" in content_text:
                try:
                    start_idx = content_text.index("{")
                    end_idx = content_text.rindex("}") + 1
                    parsed_json = json.loads(content_text[start_idx:end_idx])
                except Exception:
                    pass

        prompt_tokens = data.get("prompt_eval_count")
        completion_tokens = data.get("eval_count")

        return LLMResult(
            content=content_text,
            provider="ollama",
            model=data.get("model", self.model),
            latency_ms=latency_ms,
            parsed_json=parsed_json,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


class LocalOpenAICompatibleProvider(LLMProvider):
    """
    Client for OpenAI-compatible local servers (e.g. vLLM, LM Studio, LocalAI, llama-cpp-python).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str = "redline-llm",
        api_key: str = "local-key",
        default_timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or "local-key"
        self.default_timeout = default_timeout

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> LLMResult:
        start_time = time.perf_counter()
        req_timeout = timeout or self.default_timeout

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature if temperature is not None else 0.3,
        }

        # Check if the prompt requests JSON
        if "json" in prompt.lower() or "json" in system_prompt.lower():
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=req_timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            except httpx.ConnectError as e:
                raise ConnectionError(
                    f"Failed to connect to local LLM server at {self.base_url}. Error: " + str(e)
                ) from e
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Local LLM request timed out after {req_timeout}s: {e}") from e

            if response.status_code != 200:
                raise RuntimeError(
                    f"Local LLM API returned HTTP {response.status_code}: {response.text}"
                )

            data = response.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        choices = data.get("choices", [])
        content_text = ""
        if choices:
            content_text = choices[0].get("message", {}).get("content", "").strip()

        parsed_json = None
        try:
            parsed_json = json.loads(content_text)
        except json.JSONDecodeError:
            if "{" in content_text and "}" in content_text:
                try:
                    start_idx = content_text.index("{")
                    end_idx = content_text.rindex("}") + 1
                    parsed_json = json.loads(content_text[start_idx:end_idx])
                except Exception:
                    pass

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")

        return LLMResult(
            content=content_text,
            provider="local",
            model=data.get("model", self.model),
            latency_ms=latency_ms,
            parsed_json=parsed_json,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

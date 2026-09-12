"""
Anthropic API provider implementation using HTTPX.
"""
import json
import time
from typing import Optional

import httpx

from app.llm.provider import LLMProvider, LLMResult


class AnthropicProvider(LLMProvider):
    """
    Direct asynchronous client for Anthropic API (Claude models).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        base_url: str = "https://api.anthropic.com/v1",
        default_timeout: float = 30.0,
    ):
        if not api_key:
            raise ValueError(
                "AnthropicProvider requires a valid API key. "
                "Set ANTHROPIC_API_KEY or LLM_API_KEY in .env or environment."
            )
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
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
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "temperature": temperature if temperature is not None else 0.7,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=req_timeout) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Anthropic API returned error HTTP {response.status_code}: {response.text}"
                )

            data = response.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Extract message text from Anthropic response structure
        content_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content_text += block.get("text", "")

        parsed_json = None
        try:
            parsed_json = json.loads(content_text)
        except json.JSONDecodeError:
            pass

        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens")
        completion_tokens = usage.get("output_tokens")

        return LLMResult(
            content=content_text,
            provider="anthropic",
            model=data.get("model", self.model),
            latency_ms=latency_ms,
            parsed_json=parsed_json,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

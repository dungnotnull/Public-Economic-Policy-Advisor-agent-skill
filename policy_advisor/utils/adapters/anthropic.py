"""Anthropic Claude Messages API adapter (stdlib-only).

Calls the Claude Messages API via ``urllib``. Requires the ``ANTHROPIC_API_KEY``
environment variable (or an explicit ``api_key`` argument). When the call fails,
it raises :class:`LLMInvocationError`, which the wrapping
:class:`RetryingLLMAdapter` retries and ultimately turns into a graceful
``MockLLMAdapter`` fallback.

Reference: https://docs.anthropic.com/en/api/messages
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from config import get_settings
from ..context import LLMAdapter, LLMResponse, token_estimate
from ..errors import LLMInvocationError
from ..logging import get_logger
from ._http import http_post_json

_log = get_logger("adapters.anthropic")

_DEFAULT_BASE_URL = "https://api.anthropic.com"
_API_VERSION = "2023-06-01"


class AnthropicAdapter(LLMAdapter):
    """Real adapter for the Anthropic Claude Messages API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model or settings.llm.model
        self._base_url = (base_url or settings.llm.api_base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout if timeout is not None else settings.llm.request_timeout_seconds
        self._max_output_tokens = max_output_tokens or settings.llm.max_output_tokens
        self._temperature = temperature if temperature is not None else settings.llm.temperature

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _endpoint(self) -> str:
        return f"{self._base_url}/v1/messages"

    def _build_payload(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return {
            "model": self._model,
            "max_tokens": self._max_output_tokens,
            "temperature": self._temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

    def _build_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": _API_VERSION,
        }

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> LLMResponse:
        if not self.is_configured:
            raise LLMInvocationError("ANTHROPIC_API_KEY is not set; cannot call the Anthropic API.", recoverable=False)
        payload = self._build_payload(system_prompt, user_prompt)
        headers = self._build_headers()
        start = time.perf_counter()
        data = http_post_json(self._endpoint(), payload, headers, timeout=self._timeout)
        latency = (time.perf_counter() - start) * 1000.0

        try:
            content_blocks = data.get("content", [])
            text = "".join(b.get("text", "") for b in content_blocks if isinstance(b, dict) and b.get("type") == "text")
            usage = data.get("usage", {}) or {}
            finish = data.get("stop_reason", "stop")
            model = data.get("model", self._model)
        except Exception as exc:  # noqa: BLE001
            raise LLMInvocationError(f"malformed Anthropic response: {exc}", recoverable=False) from exc

        if not text:
            _log.warning("anthropic_empty_response", model=model, finish=finish)
        return LLMResponse(
            text=text,
            model=model,
            prompt_tokens=int(usage.get("input_tokens", 0)) or token_estimate(system_prompt + user_prompt),
            completion_tokens=int(usage.get("output_tokens", 0)) or token_estimate(text),
            finish_reason=finish or "stop",
            latency_ms=latency,
        )

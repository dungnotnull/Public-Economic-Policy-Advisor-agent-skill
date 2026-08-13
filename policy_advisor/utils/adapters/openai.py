"""OpenAI Chat Completions API adapter (stdlib-only).

Calls the OpenAI-compatible Chat Completions endpoint via ``urllib``. Requires
``OPENAI_API_KEY``. Also works with OpenAI-compatible gateways by overriding
``base_url`` (e.g. Azure OpenAI, local LLM servers exposing the same schema).

Reference: https://platform.openai.com/docs/api-reference/chat
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

_log = get_logger("adapters.openai")

_DEFAULT_BASE_URL = "https://api.openai.com"


class OpenAIAdapter(LLMAdapter):
    """Real adapter for the OpenAI Chat Completions API (and compatible gateways)."""

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
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model or settings.llm.model
        self._base_url = (base_url or settings.llm.api_base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout if timeout is not None else settings.llm.request_timeout_seconds
        self._max_output_tokens = max_output_tokens or settings.llm.max_output_tokens
        self._temperature = temperature if temperature is not None else settings.llm.temperature

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _endpoint(self) -> str:
        return f"{self._base_url}/v1/chat/completions"

    def _build_payload(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return {
            "model": self._model,
            "max_tokens": self._max_output_tokens,
            "temperature": self._temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

    def _build_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> LLMResponse:
        if not self.is_configured:
            raise LLMInvocationError("OPENAI_API_KEY is not set; cannot call the OpenAI API.", recoverable=False)
        payload = self._build_payload(system_prompt, user_prompt)
        headers = self._build_headers()
        start = time.perf_counter()
        data = http_post_json(self._endpoint(), payload, headers, timeout=self._timeout)
        latency = (time.perf_counter() - start) * 1000.0

        try:
            choices = data.get("choices", []) or []
            text = ""
            finish = "stop"
            if choices:
                msg = choices[0].get("message", {}) or {}
                text = msg.get("content", "") or ""
                finish = choices[0].get("finish_reason", "stop") or "stop"
            usage = data.get("usage", {}) or {}
            model = data.get("model", self._model)
        except Exception as exc:  # noqa: BLE001
            raise LLMInvocationError(f"malformed OpenAI response: {exc}", recoverable=False) from exc

        if not text:
            _log.warning("openai_empty_response", model=model, finish=finish)
        return LLMResponse(
            text=text,
            model=model,
            prompt_tokens=int(usage.get("prompt_tokens", 0)) or token_estimate(system_prompt + user_prompt),
            completion_tokens=int(usage.get("completion_tokens", 0)) or token_estimate(text),
            finish_reason=finish,
            latency_ms=latency,
        )

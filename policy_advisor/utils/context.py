"""LLM context management and a swappable adapter abstraction.

The skill never calls a concrete provider directly. Instead it talks to an
:class:`LLMAdapter`, which keeps the runtime testable, provider-agnostic, and
allows graceful fallback when a real model call fails (see
``MockLLMAdapter``).

Token estimation uses a conservative heuristic (~4 chars per token) that is
good enough for budgeting decisions without requiring a tokenizer dependency.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from config import get_settings
from .errors import LLMInvocationError
from .logging import get_logger

_log = get_logger("context")


# --------------------------------------------------------------------------- #
# Token estimation
# --------------------------------------------------------------------------- #
_CHARS_PER_TOKEN = 4.0


def token_estimate(text: str) -> int:
    """Return a conservative upper-bound token estimate for ``text``."""
    if not text:
        return 0
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


# --------------------------------------------------------------------------- #
# System prompt assembly
# --------------------------------------------------------------------------- #
_SYSTEM_PROMPT_HEADER = (
    "You are the Public Economic Policy Advisor, an analytical assistant that "
    "applies established public-economics frameworks (welfare economics, "
    "cost-benefit analysis, tax incidence, market-failure analysis, comparative "
    "macroeconomic schools, and modern causal-evaluation methods). You always "
    "present multiple viewpoints where evidence is contested, name the framework "
    "you are applying, and never present output as a certified professional "
    "determination."
)


def build_system_prompt(reference_snippets: Optional[List[str]] = None) -> str:
    """Compose the system prompt, injecting RAG reference snippets when present."""
    settings = get_settings()
    parts: List[str] = [_SYSTEM_PROMPT_HEADER]
    if settings.features.enable_disclaimer_injection:
        parts.append(
            "MANDATORY DISCLAIMER: every substantive response must state that the "
            "output is general/educational/analytical information, not professional "
            "advice, and recommend consulting a qualified professional for decisions "
            "with real consequences."
        )
    if reference_snippets:
        budget = settings.context_budget.max_reference_tokens
        used = 0
        included: List[str] = []
        for snippet in reference_snippets:
            est = token_estimate(snippet)
            if used + est > budget:
                _log.warning(
                    "reference_budget_exceeded",
                    snippet_tokens=est,
                    budget=budget,
                )
                break
            included.append(snippet)
            used += est
        if included:
            parts.append("GROUNDED REFERENCES (use these to support claims):\n" + "\n---\n".join(included))
    return "\n\n".join(parts)


# --------------------------------------------------------------------------- #
# LLM adapter
# --------------------------------------------------------------------------- #
@dataclass
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0.0


class LLMAdapter:
    """Abstract adapter. Subclasses implement :meth:`complete`."""

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> LLMResponse:
        raise NotImplementedError


class MockLLMAdapter(LLMAdapter):
    """Deterministic, offline adapter used for tests and graceful fallback.

    It produces a structured, framework-named placeholder that clearly marks
    itself as a fallback response so a human reviewer never mistakes it for a
    real model generation. This keeps the skill functional even when no live
    model is reachable.
    """

    def __init__(self, responder: Optional[Callable[[str, str], str]] = None) -> None:
        self._responder = responder

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> LLMResponse:
        start = time.perf_counter()
        if self._responder is not None:
            text = self._responder(system_prompt, user_prompt)
        else:
            text = (
                "[FALLBACK/MOCK-LLM] No live model adapter was configured. The skill "
                "executed its deterministic fallback path. Framework applied: structured "
                "public-economics reasoning template. User query acknowledged:\n"
                + user_prompt[:500]
            )
        latency = (time.perf_counter() - start) * 1000.0
        return LLMResponse(
            text=text,
            model="mock-llm-fallback",
            prompt_tokens=token_estimate(system_prompt + user_prompt),
            completion_tokens=token_estimate(text),
            finish_reason="fallback",
            latency_ms=latency,
        )


class RetryingLLMAdapter(LLMAdapter):
    """Wrap an adapter with bounded retries and graceful fallback.

    On a transient failure the adapter retries with exponential backoff up to
    ``Settings.llm.max_retries``. If all attempts fail and the
    ``enable_graceful_llm_fallback`` feature is on, it transparently delegates
    to a :class:`MockLLMAdapter` so the skill still returns a coherent result
    envelope rather than crashing.
    """

    def __init__(self, inner: LLMAdapter, fallback: Optional[LLMAdapter] = None) -> None:
        self._inner = inner
        self._fallback = fallback or MockLLMAdapter()
        self._log = get_logger("llm")

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> LLMResponse:
        settings = get_settings()
        last_exc: Optional[Exception] = None
        backoff = settings.llm.retry_backoff_base_seconds
        for attempt in range(1, settings.llm.max_retries + 1):
            try:
                return self._inner.complete(system_prompt, user_prompt, **kwargs)
            except Exception as exc:  # noqa: BLE001 - we re-raise after exhausting retries
                last_exc = exc
                recoverable = getattr(exc, "recoverable", True)
                self._log.warning(
                    "llm_attempt_failed",
                    attempt=attempt,
                    error=str(exc),
                    recoverable=recoverable,
                )
                # Non-recoverable errors (e.g. missing API key, malformed request)
                # must not be retried - fail fast to the fallback or raise.
                if not recoverable or attempt >= settings.llm.max_retries:
                    break
                time.sleep(backoff)
                backoff *= settings.llm.retry_backoff_base_seconds

        if settings.features.enable_graceful_llm_fallback:
            self._log.warning("llm_fallback_engaged", attempts=settings.llm.max_retries)
            return self._fallback.complete(system_prompt, user_prompt, **kwargs)
        raise LLMInvocationError(
            f"LLM call failed after {settings.llm.max_retries} attempts: {last_exc}",
            attempts=settings.llm.max_retries,
        )

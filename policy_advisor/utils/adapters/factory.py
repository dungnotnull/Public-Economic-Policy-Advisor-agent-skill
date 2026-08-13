"""LLM adapter factory.

Selects a concrete adapter from configuration and available credentials. The
default ``provider="auto"`` resolution order is:

1. ``anthropic`` if ``ANTHROPIC_API_KEY`` is set.
2. ``openai`` if ``OPENAI_API_KEY`` is set.
3. ``mock`` (offline) otherwise - so the skill always runs.

Explicit ``provider`` settings (``"anthropic"``, ``"openai"``, ``"mock"``)
override auto-detection. The chosen adapter is wrapped by
:class:`RetryingLLMAdapter` at the registry layer for retries + graceful
fallback.
"""

from __future__ import annotations

import os
from typing import Optional

from config import Settings, get_settings
from ..context import LLMAdapter, MockLLMAdapter
from ..logging import get_logger

_log = get_logger("adapters.factory")


def _has_key(env_name: str) -> bool:
    return bool(os.environ.get(env_name))


def resolve_provider(settings: Optional[Settings] = None) -> str:
    """Return the provider name that will be used, honouring explicit choice."""
    settings = settings or get_settings()
    provider = (settings.llm.provider or "auto").lower()
    if provider in {"anthropic", "openai", "mock"}:
        return provider
    # auto
    if _has_key("ANTHROPIC_API_KEY"):
        return "anthropic"
    if _has_key("OPENAI_API_KEY"):
        return "openai"
    return "mock"


def make_llm_adapter(settings: Optional[Settings] = None) -> LLMAdapter:
    """Construct and return the selected LLM adapter (unwrapped)."""
    settings = settings or get_settings()
    provider = resolve_provider(settings)
    _log.info("adapter_resolved", provider=provider, model=settings.llm.model)

    if provider == "anthropic":
        from .anthropic import AnthropicAdapter
        return AnthropicAdapter()
    if provider == "openai":
        from .openai import OpenAIAdapter
        return OpenAIAdapter()
    return MockLLMAdapter()

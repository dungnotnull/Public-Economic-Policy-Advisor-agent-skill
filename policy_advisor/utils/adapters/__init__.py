"""Pluggable, production-grade LLM adapters.

The skill never calls a concrete provider directly from business logic; it talks
to an :class:`~policy_advisor.utils.context.LLMAdapter`. This package ships real,
functional adapters for the major providers (Anthropic Claude, OpenAI) plus a
factory that selects one based on configuration and available credentials.

All adapters use only the Python standard library (``urllib``) so the skill
remains dependency-free. When no provider credentials are present, the factory
returns the offline :class:`MockLLMAdapter`, guaranteeing the skill always runs.

Usage::

    from policy_advisor.utils.adapters import make_llm_adapter
    llm = make_llm_adapter()           # auto-selects provider or mock
    response = llm.complete(system_prompt, user_prompt)
"""

from .anthropic import AnthropicAdapter
from .openai import OpenAIAdapter
from .factory import make_llm_adapter, resolve_provider

__all__ = [
    "AnthropicAdapter",
    "OpenAIAdapter",
    "make_llm_adapter",
    "resolve_provider",
]

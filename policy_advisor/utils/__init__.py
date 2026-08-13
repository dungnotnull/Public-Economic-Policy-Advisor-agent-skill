"""Utility helpers: structured logging, error taxonomy, and LLM context
management used across the skill runtime."""

from .logging import get_logger, StructuredLogger
from .errors import (
    SkillError,
    ConfigurationError,
    RoutingError,
    ToolExecutionError,
    LLMInvocationError,
    ReferenceLoadError,
)
from .context import LLMAdapter, MockLLMAdapter, build_system_prompt, token_estimate
from .synthesis import build_narrative, synthesize_narrative
from .adapters import AnthropicAdapter, OpenAIAdapter, make_llm_adapter, resolve_provider

__all__ = [
    "get_logger",
    "StructuredLogger",
    "SkillError",
    "ConfigurationError",
    "RoutingError",
    "ToolExecutionError",
    "LLMInvocationError",
    "ReferenceLoadError",
    "LLMAdapter",
    "MockLLMAdapter",
    "build_system_prompt",
    "token_estimate",
    "build_narrative",
    "synthesize_narrative",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "make_llm_adapter",
    "resolve_provider",
]

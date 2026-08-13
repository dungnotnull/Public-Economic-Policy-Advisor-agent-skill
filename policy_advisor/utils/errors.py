"""Error taxonomy for the skill runtime.

All skill-raised exceptions derive from :class:`SkillError` so callers can
catch the entire family with a single ``except`` clause while still
discriminating by subtype when finer handling is required.
"""

from __future__ import annotations


class SkillError(Exception):
    """Base class for every error raised by the skill runtime."""

    default_message = "An error occurred while executing the public-economic-policy-advisor skill."

    def __init__(self, message: str = "", *, recoverable: bool = True) -> None:
        super().__init__(message or self.default_message)
        self.recoverable = recoverable


class ConfigurationError(SkillError):
    default_message = "Invalid configuration supplied to the skill runtime."


class RoutingError(SkillError):
    default_message = "The chain-of-thought router could not resolve a target sub-advisor."


class ToolExecutionError(SkillError):
    default_message = "A registered tool failed during execution."

    def __init__(self, message: str = "", *, tool: str = "", recoverable: bool = True) -> None:
        super().__init__(message, recoverable=recoverable)
        self.tool = tool


class LLMInvocationError(SkillError):
    default_message = "The backing language-model call failed."

    def __init__(self, message: str = "", *, attempts: int = 0, recoverable: bool = True) -> None:
        super().__init__(message, recoverable=recoverable)
        self.attempts = attempts


class ReferenceLoadError(SkillError):
    default_message = "A reference file could not be loaded for RAG grounding."


class ValidationError(SkillError):
    default_message = "Skill input or output failed schema validation."

"""Shared base for sub-advisors and the execution context they share."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import Settings, get_settings
from ..hooks import EventBus, LifecycleHookBus, StateStore
from ..tools import ToolRegistry
from ..utils.context import LLMAdapter, MockLLMAdapter
from ..utils.logging import StructuredLogger, get_logger

DISCLAIMER = (
    "This output is general, educational, and analytical information produced by the "
    "Public Economic Policy Advisor skill. It is not professional advice and must not be "
    "treated as a certified determination, legal opinion, or guaranteed forecast. For "
    "decisions with real consequences, consult a qualified professional (e.g. economist, "
    "fiscal analyst, or licensed advisor)."
)


@dataclass
class SubAdvisorContext:
    """Shared dependencies injected into every sub-advisor."""

    settings: Settings = field(default_factory=get_settings)
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    llm: LLMAdapter = field(default_factory=MockLLMAdapter)
    lifecycle: LifecycleHookBus = field(default_factory=LifecycleHookBus)
    events: EventBus = field(default_factory=EventBus)
    state: StateStore = field(default_factory=StateStore)
    logger: StructuredLogger = field(default_factory=lambda: get_logger("advisor"))
    references: Dict[str, str] = field(default_factory=dict)


class SubAdvisor:
    """Abstract sub-advisor. Subclasses set ``name`` and ``formats``."""

    name: str = "base"
    formats: List[str] = []
    keywords: List[str] = []

    def __init__(self, ctx: SubAdvisorContext) -> None:
        self.ctx = ctx

    def serves(self, requested_format: str) -> bool:
        return requested_format in self.formats

    def matches_query(self, query: str) -> int:
        """Return a relevance score for free-text routing tie-breaking."""
        q = query.lower()
        return sum(1 for kw in self.keywords if kw in q)

    def handle(self, invocation) -> Any:  # pragma: no cover - abstract
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Helpers shared by all sub-advisors
    # ------------------------------------------------------------------ #
    def _grounded_snippets(self, requested: Optional[List[str]] = None) -> List[str]:
        if not self.ctx.settings.features.enable_rag_reference_loading:
            return []
        refs = self.ctx.references
        keys = requested or list(refs)
        return [refs[k] for k in keys if k in refs]

    def _disclaimer(self) -> str:
        return DISCLAIMER if self.ctx.settings.features.enable_disclaimer_injection else ""

    def _llm_synthesize(self, system_prompt: str, user_prompt: str) -> str:
        if not self.ctx.settings.features.enable_sub_advisor_delegation:
            return ""
        try:
            resp = self.ctx.llm.complete(system_prompt, user_prompt)
            return resp.text
        except Exception as exc:  # noqa: BLE001
            self.ctx.logger.warning("llm_synthesis_failed", sub_advisor=self.name, error=str(exc))
            return ""

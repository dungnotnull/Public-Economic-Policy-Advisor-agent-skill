"""Skill registry.

A modular registry pattern: skills (sub-advisors) and tools are registered,
resolved, executed, and validated through a single orchestrator. This is the
runtime mirror of the human-readable ``SKILL.md`` registry documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import Settings, get_settings
from config.schema import SkillInvocation, SkillResult
from .grounding import load_references
from .hooks import EventBus, LifecycleHookBus, LifecyclePhase, StateStore
from .router import ChainOfThoughtRouter, RoutingDecision
from .sub_advisors import SubAdvisor, SubAdvisorContext, default_sub_advisors
from .tools import ToolRegistry, register_default_tools
from .utils.context import LLMAdapter, MockLLMAdapter, RetryingLLMAdapter
from .utils.adapters import make_llm_adapter
from .utils.errors import SkillError
from .utils.logging import get_logger

_log = get_logger("registry")


@dataclass
class SkillRegistry:
    """Top-level orchestrator that wires tools, sub-advisors, and the router."""

    settings: Settings = field(default_factory=get_settings)
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    llm: LLMAdapter = field(default_factory=make_llm_adapter)
    lifecycle: LifecycleHookBus = field(default_factory=LifecycleHookBus)
    events: EventBus = field(default_factory=EventBus)
    state: StateStore = field(default_factory=StateStore)
    sub_advisors: List[SubAdvisor] = field(default_factory=list)
    router: Optional[ChainOfThoughtRouter] = None
    _initialized: bool = False

    def initialize(self) -> "SkillRegistry":
        if self._initialized:
            return self
        register_default_tools(self.tools)
        refs = load_references() if self.settings.features.enable_rag_reference_loading else {}
        ctx = SubAdvisorContext(
            settings=self.settings,
            tools=self.tools,
            llm=RetryingLLMAdapter(self.llm) if self.settings.features.enable_graceful_llm_fallback else self.llm,
            lifecycle=self.lifecycle,
            events=self.events,
            state=self.state,
            logger=get_logger("advisor"),
            references=refs,
        )
        self.sub_advisors = default_sub_advisors(ctx)
        self.router = ChainOfThoughtRouter(self.sub_advisors)
        self._initialized = True
        _log.info("registry_initialized", tools=self.tools.available(), sub_advisors=[a.name for a in self.sub_advisors])
        return self

    # ------------------------------------------------------------------ #
    def invoke(self, invocation: SkillInvocation) -> SkillResult:
        if not self._initialized:
            self.initialize()
        assert self.router is not None
        request_id = invocation.request_id
        warnings: List[str] = []
        self.lifecycle.fire(LifecyclePhase.INTAKE, request_id, {"query": invocation.user_query})
        self.events.emit("skill.invocation.received", request_id=request_id, format=invocation.requested_format)

        try:
            self.lifecycle.fire(LifecyclePhase.ROUTING, request_id, {})
            decision: RoutingDecision = self.router.route(invocation)
            sub_advisor = self.router.resolve(invocation)
            self.events.emit("skill.route.resolved", request_id=request_id, sub_advisor=sub_advisor.name)

            self.lifecycle.fire(LifecyclePhase.TOOL_EXECUTION, request_id, {"sub_advisor": sub_advisor.name})
            tools_before = len(self.tools.invocation_log())
            report = sub_advisor.handle(invocation)
            tools_after = self.tools.invocation_log()[tools_before:]
            self.events.emit("skill.report.generated", request_id=request_id, report=type(report).__name__)

            self.lifecycle.fire(LifecyclePhase.SYNTHESIS, request_id, {})
            result = SkillResult.from_report(
                report,
                route_taken=sub_advisor.name,
                sub_advisors_used=[sub_advisor.name],
                tools_used=[i["tool"] for i in tools_after],
                warnings=warnings,
            )
            self.state.set(request_id, result.to_json())
            self.lifecycle.fire(LifecyclePhase.OUTPUT, request_id, {"status": "ok"})
            self.events.emit("skill.invocation.completed", request_id=request_id, status="ok")
            return result
        except SkillError as exc:
            _log.warning("skill_invocation_failed", request_id=request_id, error=str(exc))
            self.lifecycle.fire(LifecyclePhase.OUTPUT, request_id, {"status": "degraded"})
            self.events.emit("skill.invocation.degraded", request_id=request_id, error=str(exc))
            return _degraded_result(invocation, str(exc))
        except Exception as exc:  # noqa: BLE001 - last-resort safety net
            _log.error("skill_invocation_error", request_id=request_id, error=str(exc))
            self.lifecycle.fire(LifecyclePhase.OUTPUT, request_id, {"status": "error"})
            self.events.emit("skill.invocation.error", request_id=request_id, error=str(exc))
            return _degraded_result(invocation, f"Unexpected error: {exc}", status="error")


def _degraded_result(invocation: SkillInvocation, message: str, status: str = "degraded") -> SkillResult:
    from .sub_advisors.base import DISCLAIMER

    return SkillResult(
        request_id=invocation.request_id,
        status=status,
        format=invocation.requested_format,
        payload={
            "user_query": invocation.user_query,
            "message": message,
            "guidance": (
                "The skill could not fully process this request. If the issue persists, "
                "refine the requested_format or supply richer context (jurisdiction, "
                "elasticities, items, evaluation_context)."
            ),
        },
        warnings=[message],
        disclaimer=DISCLAIMER,
    )


# --------------------------------------------------------------------------- #
# Process-wide singleton accessor
# --------------------------------------------------------------------------- #
_REGISTRY: Optional[SkillRegistry] = None


def get_registry(llm: Optional[LLMAdapter] = None, settings: Optional[Settings] = None) -> SkillRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = SkillRegistry(settings=settings or get_settings(), llm=llm or make_llm_adapter(settings))
        _REGISTRY.initialize()
    return _REGISTRY


def reset_registry() -> None:
    global _REGISTRY
    _REGISTRY = None

"""Public Economic Policy Advisor - production skill runtime.

A modular, registry-based skill that applies established public-economics
frameworks (welfare economics, cost-benefit analysis, tax incidence,
market-failure analysis, comparative macroeconomic schools, and modern
causal-evaluation methods) to policy questions, always presenting multiple
viewpoints where evidence is contested.

Public entry points:

* :func:`advise` -- high-level convenience: build an invocation, run the
  registry, and return a :class:`SkillResult`.
* :class:`SkillRegistry` -- the orchestrator (tools + sub-advisors + router +
  hooks + events + state).
* :func:`get_registry` -- process-wide singleton accessor.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from config import Settings, get_settings
from config.schema import SkillInvocation, SkillResult
from .citations import citations_for, evidence_base_for, all_papers
from .grounding import load_references
from .hooks import EventBus, LifecycleHookBus, StateStore
from .router import ChainOfThoughtRouter
from .skill_registry import SkillRegistry, get_registry, reset_registry
from .sub_advisors import (
    EmpiricalAdvisor,
    FiscalAdvisor,
    MacroAdvisor,
    SubAdvisor,
    SubAdvisorContext,
    WelfareAdvisor,
    default_sub_advisors,
)
from .tools import (
    CausalEvaluationTool,
    ComparativeSchoolsTool,
    CostBenefitAnalysisTool,
    MarketFailureDiagnosticTool,
    TaxIncidenceTool,
    Tool,
    ToolRegistry,
    register_default_tools,
)
from .utils.context import LLMAdapter, LLMResponse, MockLLMAdapter, RetryingLLMAdapter, build_system_prompt, token_estimate
from .utils.synthesis import build_narrative, synthesize_narrative
from .utils.adapters import AnthropicAdapter, OpenAIAdapter, make_llm_adapter, resolve_provider
from .utils.errors import (
    ConfigurationError,
    LLMInvocationError,
    ReferenceLoadError,
    RoutingError,
    SkillError,
    ToolExecutionError,
)
from .utils.logging import StructuredLogger, get_logger

__version__ = "1.0.0"

__all__ = [
    "advise",
    "SkillRegistry",
    "get_registry",
    "reset_registry",
    "SkillInvocation",
    "SkillResult",
    "ChainOfThoughtRouter",
    "Tool",
    "ToolRegistry",
    "register_default_tools",
    "CostBenefitAnalysisTool",
    "TaxIncidenceTool",
    "MarketFailureDiagnosticTool",
    "ComparativeSchoolsTool",
    "CausalEvaluationTool",
    "SubAdvisor",
    "SubAdvisorContext",
    "FiscalAdvisor",
    "MacroAdvisor",
    "WelfareAdvisor",
    "EmpiricalAdvisor",
    "default_sub_advisors",
    "LLMAdapter",
    "MockLLMAdapter",
    "RetryingLLMAdapter",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "make_llm_adapter",
    "resolve_provider",
    "LLMResponse",
    "build_system_prompt",
    "token_estimate",
    "build_narrative",
    "synthesize_narrative",
    "load_references",
    "citations_for",
    "evidence_base_for",
    "all_papers",
    "EventBus",
    "LifecycleHookBus",
    "StateStore",
    "SkillError",
    "ConfigurationError",
    "RoutingError",
    "ToolExecutionError",
    "LLMInvocationError",
    "ReferenceLoadError",
    "get_settings",
    "Settings",
    "get_logger",
    "StructuredLogger",
    "__version__",
]


def advise(
    user_query: str,
    requested_format: str = "policy-memo",
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    llm: Optional[LLMAdapter] = None,
) -> SkillResult:
    """One-call entry point: run a single policy query through the skill."""
    invocation = SkillInvocation(
        request_id=request_id or f"req-{uuid.uuid4().hex[:12]}",
        user_query=user_query,
        requested_format=requested_format,
        context=context or {},
    )
    registry = get_registry(llm=llm)
    return registry.invoke(invocation)

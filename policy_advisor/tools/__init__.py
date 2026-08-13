"""Tool package: schema-driven, executable domain tools.

Each tool implements a public-economics framework as a deterministic,
side-effect-free Python function with a declared JSON Schema for its inputs
and outputs. Tools are registered in a registry and are dynamically invocable
by sub-advisors. Using real, functional implementations (rather than
prompt-only "tools") guarantees consistent, auditable results and lets the
skill degrade gracefully when the backing LLM is unavailable.
"""

from .base import Tool, ToolRegistry, ToolResult, get_tool_registry
from .cba_tool import CostBenefitAnalysisTool
from .incidence_tool import TaxIncidenceTool
from .market_failure_tool import MarketFailureDiagnosticTool
from .schools_tool import ComparativeSchoolsTool
from .causal_eval_tool import CausalEvaluationTool

__all__ = [
    "Tool",
    "ToolRegistry",
    "ToolResult",
    "get_tool_registry",
    "CostBenefitAnalysisTool",
    "TaxIncidenceTool",
    "MarketFailureDiagnosticTool",
    "ComparativeSchoolsTool",
    "CausalEvaluationTool",
    "register_default_tools",
]


def register_default_tools(registry: "ToolRegistry | None" = None) -> "ToolRegistry":
    """Register the built-in tool set and return the registry."""
    reg = registry or get_tool_registry()
    for tool_cls in (
        CostBenefitAnalysisTool,
        TaxIncidenceTool,
        MarketFailureDiagnosticTool,
        ComparativeSchoolsTool,
        CausalEvaluationTool,
    ):
        reg.register(tool_cls())
    return reg

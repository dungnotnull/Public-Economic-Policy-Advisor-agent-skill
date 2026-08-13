"""Causal policy-evaluation tool.

Recommends an empirical identification strategy (RCT, difference-in-differences,
regression discontinuity, instrumental variables, or natural experiment) for
evaluating a policy, with the method rationale, data requirements, and threats
to validity. The recommendation is rule-based from the evaluation context so
it is reproducible and auditable.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Tool, ToolResult

_METHODS: Dict[str, Dict[str, Any]] = {
    "RCT": {
        "rationale": "Gold standard for internal validity when the intervention can be randomly assigned and ethical.",
        "data_requirements": ["random assignment records", "baseline and follow-up outcome data", "compliance/attrition tracking"],
        "threats": ["external validity / generalisability", "attrition", "SUTVA / spillovers", "ethical or political constraints"],
    },
    "DiD": {
        "rationale": "Uses a comparison group over time to net out common trends when random assignment is impossible.",
        "data_requirements": ["pre/post outcome series for treated and control groups", "parallel-trends evidence"],
        "threats": ["parallel-trends violation", "composition changes", "confounding policy changes", "anticipation effects"],
    },
    "RDD": {
        "rationale": "Exploits a sharp eligibility cutoff to estimate local causal effects near the threshold.",
        "data_requirements": ["running variable", "outcome near the cutoff", "cutoff rule documentation"],
        "threats": ["manipulation of the running variable", "local-only validity", "small-sample near cutoff", "sorting around threshold"],
    },
    "IV": {
        "rationale": "Uses an exogenous instrument to isolate variation free of endogeneity.",
        "data_requirements": ["valid instrument", "instrument relevance evidence", "exclusion-restriction argument"],
        "threats": ["weak instruments", "exclusion restriction violation", "local average treatment effect interpretation"],
    },
    "natural experiment": {
        "rationale": "Exploits plausibly exogenous shocks when controlled designs are unavailable.",
        "data_requirements": ["clearly exogenous shock", "treatment and comparison units", "pre-trends"],
        "threats": ["endogeneity of the shock", "selection into exposure", "measurement of exposure"],
    },
}


def _recommend_method(context: Dict[str, Any]) -> str:
    can_randomize = context.get("can_randomize", False)
    has_cutoff = context.get("has_eligibility_cutoff", False)
    has_panel = context.get("has_panel_data", False)
    has_instrument = context.get("has_instrument", False)
    has_shock = context.get("has_exogenous_shock", False)

    if can_randomize:
        return "RCT"
    if has_cutoff:
        return "RDD"
    if has_panel:
        return "DiD"
    if has_instrument:
        return "IV"
    if has_shock:
        return "natural experiment"
    return "DiD"


class CausalEvaluationTool(Tool):
    name = "causal_evaluation"
    description = (
        "Recommend a causal-identification strategy for evaluating a policy, "
        "with rationale, data requirements, and threats to validity."
    )
    input_schema = {
        "type": "object",
        "required": ["policy_under_evaluation"],
        "properties": {
            "policy_under_evaluation": {"type": "string"},
            "evaluation_context": {"type": "object"},
        },
    }
    output_schema = {
        "type": "object",
        "required": ["policy_under_evaluation", "recommended_method", "method_rationale", "data_requirements", "threats_to_validity"],
        "properties": {
            "policy_under_evaluation": {"type": "string"},
            "recommended_method": {"type": "string"},
            "method_rationale": {"type": "string"},
            "identification_strategy": {"type": "string"},
            "data_requirements": {"type": "array"},
            "threats_to_validity": {"type": "array"},
            "confidence": {"type": "string"},
        },
    }

    def execute(self, policy_under_evaluation: str, evaluation_context: Dict[str, Any] | None = None, **_: Any) -> ToolResult:
        ctx = evaluation_context or {}
        method = _recommend_method(ctx)
        spec = _METHODS[method]
        identification = {
            "RCT": "Random assignment of the policy across eligible units.",
            "DiD": "Compare change in outcomes for treated vs control units, assuming parallel pre-trends.",
            "RDD": "Compare outcomes just above vs just below the eligibility cutoff.",
            "IV": "Use an exogenous instrument to isolate compliant variation in treatment.",
            "natural experiment": "Compare units differentially exposed to an exogenous shock.",
        }[method]
        confidence = "high" if method == "RCT" else "medium" if method in {"DiD", "RDD"} else "low"
        return ToolResult(
            tool=self.name,
            ok=True,
            output={
                "policy_under_evaluation": policy_under_evaluation,
                "recommended_method": method,
                "method_rationale": spec["rationale"],
                "identification_strategy": identification,
                "data_requirements": spec["data_requirements"],
                "threats_to_validity": spec["threats"],
                "confidence": confidence,
            },
        )

"""Cost-benefit analysis tool (welfare economics).

Implements a structured, reproducible CBA scaffold: it normalises benefit/cost
items, computes a net present-value-style aggregate using caller-supplied
weights, and flags distributional and uncertainty considerations. The numbers
are qualitative magnitudes rather than fabricated currency figures, which
keeps the tool honest and avoids presenting invented precision.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Tool, ToolResult

_MAGNITUDE_RANK = {"negligible": 0.0, "small": 0.25, "moderate": 0.5, "large": 0.75, "very large": 1.0}
_CONFIDENCE_WEIGHT = {"low": 0.5, "medium": 0.8, "high": 1.0}


class CostBenefitAnalysisTool(Tool):
    name = "cost_benefit_analysis"
    description = (
        "Structure a policy proposal into benefit/cost items, weigh them by "
        "magnitude and confidence, and return a transparent welfare-economics "
        "summary with an explicit recommendation rule."
    )
    input_schema = {
        "type": "object",
        "required": ["policy_name", "items"],
        "properties": {
            "policy_name": {"type": "string"},
            "jurisdiction": {"type": "string"},
            "items": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["category", "description", "estimated_magnitude", "direction"],
                    "properties": {
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                        "estimated_magnitude": {
                            "type": "string",
                            "enum": list(_MAGNITUDE_RANK),
                        },
                        "direction": {"type": "string", "enum": ["benefit", "cost"]},
                        "confidence": {"type": "string", "enum": list(_CONFIDENCE_WEIGHT)},
                    },
                },
            },
            "discount_note": {"type": "string"},
        },
    }
    output_schema = {
        "type": "object",
        "required": ["policy_name", "net_score", "verdict", "items_scored"],
        "properties": {
            "policy_name": {"type": "string"},
            "net_score": {"type": "number"},
            "verdict": {"type": "string"},
            "items_scored": {"type": "array"},
            "distributional_flags": {"type": "array"},
            "uncertainty_flags": {"type": "array"},
        },
    }

    def execute(self, policy_name: str, items: List[Dict[str, Any]], jurisdiction: str = "", discount_note: str = "", **_: Any) -> ToolResult:
        scored: List[Dict[str, Any]] = []
        net = 0.0
        distributional_flags: List[str] = []
        uncertainty_flags: List[str] = []

        for item in items:
            mag = _MAGNITUDE_RANK.get(item["estimated_magnitude"], 0.5)
            conf = _CONFIDENCE_WEIGHT.get(item.get("confidence", "medium"), 0.8)
            sign = 1.0 if item["direction"] == "benefit" else -1.0
            contribution = sign * mag * conf
            net += contribution
            scored.append({**item, "weighted_contribution": round(contribution, 3)})
            if "distribution" in item["category"].lower() or "equity" in item["description"].lower():
                distributional_flags.append(item["description"])
            if item.get("confidence", "medium") == "low":
                uncertainty_flags.append(item["description"])

        if net > 0.5:
            verdict = "welfare-positive: aggregate weighted benefits clearly exceed costs"
        elif net > 0.0:
            verdict = "marginally welfare-positive: benefits modestly exceed costs; sensitivity analysis recommended"
        elif net > -0.5:
            verdict = "approximately welfare-neutral: benefits and costs roughly balanced"
        else:
            verdict = "welfare-negative: aggregate weighted costs exceed benefits"

        output = {
            "policy_name": policy_name,
            "jurisdiction": jurisdiction,
            "net_score": round(net, 3),
            "verdict": verdict,
            "items_scored": scored,
            "distributional_flags": distributional_flags,
            "uncertainty_flags": uncertainty_flags,
            "discount_note": discount_note or "No explicit discount rate supplied; treat magnitudes as ordinal welfare weights, not monetary NPV.",
        }
        return ToolResult(tool=self.name, ok=True, output=output)

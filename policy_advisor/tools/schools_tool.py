"""Comparative macroeconomic schools tool.

Given a policy question, returns the contrasting positions of the major
schools of thought (Keynesian, Monetarist, New Classical, Supply-side, and a
post-Keynesian/institutional voice) so the skill can present a balanced,
multi-viewpoint summary rather than a single contested answer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Tool, ToolResult

_SCHOOLS: Dict[str, Dict[str, str]] = {
    "Keynesian": {
        "position": "Active fiscal and monetary stabilisation can reduce output gaps and unemployment.",
        "key_argument": "Sticky prices/wages and aggregate-demand shortfalls justify countercyclical policy.",
        "caveats": "Risks debt accumulation and time lags; crowding-out debated.",
    },
    "Monetarist": {
        "position": "Stable money-growth rules outperform discretionary fine-tuning.",
        "key_argument": "Inflation is ultimately a monetary phenomenon; long-run Phillips curve is vertical.",
        "caveats": "Velocity instability has weakened simple money-growth targeting in recent decades.",
    },
    "New Classical": {
        "position": "Systematic policy has limited real effects once agents form rational expectations.",
        "key_argument": "The Lucas critique: structural parameters change under new policy regimes.",
        "caveats": "May understate nominal rigidities and short-run real effects observed empirically.",
    },
    "Supply-side": {
        "position": "Lower marginal tax rates and lighter regulation expand the productive base.",
        "key_argument": "High marginal rates distort labour/capital supply and avoidance; Laffer-curve effects near high rates.",
        "caveats": "Revenue feedback is usually modest at typical OECD rates; distributional effects can be regressive.",
    },
    "Institutional/Post-Keynesian": {
        "position": "Institutions, uncertainty, and financial fragility shape real policy outcomes.",
        "key_argument": "History and path-dependence matter; models should account for financial instability and distribution.",
        "caveats": "Harder to formalise; forecasts less precise.",
    },
}


class ComparativeSchoolsTool(Tool):
    name = "comparative_schools"
    description = (
        "Return the contrasting positions of major macroeconomic schools on a "
        "policy question, for balanced multi-viewpoint presentation."
    )
    input_schema = {
        "type": "object",
        "required": ["policy_question"],
        "properties": {
            "policy_question": {"type": "string"},
            "schools": {"type": "array", "items": {"type": "string"}},
        },
    }
    output_schema = {
        "type": "object",
        "required": ["policy_question", "viewpoints"],
        "properties": {
            "policy_question": {"type": "string"},
            "viewpoints": {"type": "array"},
            "contested": {"type": "boolean"},
        },
    }

    def execute(self, policy_question: str, schools: List[str] | None = None, **_: Any) -> ToolResult:
        selected = schools or list(_SCHOOLS)
        viewpoints: List[Dict[str, Any]] = []
        for name in selected:
            spec = _SCHOOLS.get(name)
            if not spec:
                continue
            viewpoints.append({"school": name, **spec})
        contested = len(viewpoints) >= 2
        return ToolResult(
            tool=self.name,
            ok=True,
            output={
                "policy_question": policy_question,
                "viewpoints": viewpoints,
                "contested": contested,
            },
        )

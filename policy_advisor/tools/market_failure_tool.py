"""Market-failure diagnostic tool.

Applies the canonical market-failure framework (externalities, public goods,
information asymmetry, market power, distributional concerns) as a checklist
to a described situation and returns the diagnosed failure types with the
intervention rationale each implies.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Tool, ToolResult

# Each failure type maps to diagnostic signals and the intervention it justifies.
_FAILURE_TYPES: Dict[str, Dict[str, Any]] = {
    "negative_externality": {
        "signals": ["pollution", "emission", "spillover cost", "third-party harm", "congestion"],
        "intervention": "Pigouvian tax, regulation, or tradable permits to internalise the external cost.",
    },
    "positive_externality": {
        "signals": ["spillover benefit", "vaccination", "education", "rd spillover", "network effect"],
        "intervention": "Subsidy, public provision, or intellectual-property protection to restore under-provision.",
    },
    "public_good": {
        "signals": ["non-excludable", "non-rival", "free rider", "national defense", "clean air", "basic research"],
        "intervention": "Public provision or financing because private markets under-supply non-excludable goods.",
    },
    "information_asymmetry": {
        "signals": ["lemons", "adverse selection", "hidden information", "moral hazard", "asymmetric", "credence good"],
        "intervention": "Mandatory disclosure, quality standards, licensing, or insurance pooling.",
    },
    "market_power": {
        "signals": ["monopoly", "oligopoly", "dominant firm", "barrier to entry", "price fixing", "natural monopoly"],
        "intervention": "Antitrust enforcement, price regulation, or public ownership for natural monopolies.",
    },
    "distributional_equity": {
        "signals": ["inequality", "poverty", "fairness", "redistribution", "equity", "social safety net"],
        "intervention": "Progressive taxation and targeted transfers (equity is a value judgement, not a pure efficiency failure).",
    },
    "coordination_failure": {
        "signals": ["network", "standards", "lock-in", "underdevelopment trap", "self-fulfilling"],
        "intervention": "Standard-setting, infrastructure, or strategic state coordination.",
    },
}


class MarketFailureDiagnosticTool(Tool):
    name = "market_failure_diagnostic"
    description = (
        "Diagnose which market-failure categories apply to a described situation "
        "and return the intervention each one justifies."
    )
    input_schema = {
        "type": "object",
        "required": ["situation"],
        "properties": {
            "situation": {"type": "string"},
            "proposed_intervention": {"type": "string"},
        },
    }
    output_schema = {
        "type": "object",
        "required": ["diagnosed_failures", "intervention_rationale"],
        "properties": {
            "diagnosed_failures": {"type": "array"},
            "intervention_rationale": {"type": "array"},
            "no_failure_found": {"type": "boolean"},
            "notes": {"type": "array"},
        },
    }

    def execute(self, situation: str, proposed_intervention: str = "", **_: Any) -> ToolResult:
        text = situation.lower()
        diagnosed: List[Dict[str, Any]] = []
        rationale: List[Dict[str, Any]] = []
        for ftype, spec in _FAILURE_TYPES.items():
            matched = [s for s in spec["signals"] if s in text]
            if matched:
                diagnosed.append({"failure_type": ftype, "matched_signals": matched})
                rationale.append({
                    "failure_type": ftype,
                    "justified_intervention": spec["intervention"],
                    "matched_signals": matched,
                })

        notes: List[str] = []
        no_failure = not diagnosed
        if no_failure:
            notes.append(
                "No clear market-failure signal detected. Intervention may still be justified on "
                "distributional grounds, but a pure efficiency case is not supported by the supplied description."
            )
        if proposed_intervention and not no_failure:
            notes.append(
                f"Proposed intervention '{proposed_intervention}' should be checked against the diagnosed "
                "failure(s): intervention should target the specific failure, not be broader than necessary."
            )
        notes.append("Distributional equity is a normative judgement; flag it separately from efficiency failures.")

        return ToolResult(
            tool=self.name,
            ok=True,
            output={
                "diagnosed_failures": diagnosed,
                "intervention_rationale": rationale,
                "no_failure_found": no_failure,
                "notes": notes,
            },
        )

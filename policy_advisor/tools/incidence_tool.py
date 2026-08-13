"""Tax & subsidy incidence tool.

Models who really bears the burden of a tax or subsidy based on relative
elasticities of supply and demand -- the core of Harberger-style incidence
analysis. The tool computes the buyer-side and seller-side shares of the
burden (or benefit, for subsidies) from caller-supplied elasticity estimates,
states the assumptions explicitly, and flags distributional consequences.
"""

from __future__ import annotations

from typing import Any, Dict

from .base import Tool, ToolResult


class TaxIncidenceTool(Tool):
    name = "tax_incidence"
    description = (
        "Compute the economic incidence of a tax or subsidy from supply and "
        "demand elasticities, returning buyer-side and seller-side burden "
        "shares plus distributional flags."
    )
    input_schema = {
        "type": "object",
        "required": ["instrument", "supply_elasticity", "demand_elasticity"],
        "properties": {
            "instrument": {"type": "string"},
            "jurisdiction": {"type": "string"},
            "supply_elasticity": {"type": "number"},
            "demand_elasticity": {"type": "number"},
            "is_subsidy": {"type": "boolean"},
            "affected_groups": {"type": "array", "items": {"type": "string"}},
        },
    }
    output_schema = {
        "type": "object",
        "required": ["instrument", "buyer_share", "seller_share", "incidence_summary"],
        "properties": {
            "instrument": {"type": "string"},
            "buyer_share": {"type": "number"},
            "seller_share": {"type": "number"},
            "incidence_summary": {"type": "string"},
            "distributional_effects": {"type": "array"},
            "welfare_effects": {"type": "array"},
            "caveats": {"type": "array"},
        },
    }

    def execute(
        self,
        instrument: str,
        supply_elasticity: float,
        demand_elasticity: float,
        jurisdiction: str = "",
        is_subsidy: bool = False,
        affected_groups: list | None = None,
        **_: Any,
    ) -> ToolResult:
        affected_groups = affected_groups or []
        es = abs(supply_elasticity)
        ed = abs(demand_elasticity)
        denom = es + ed
        if denom == 0:
            buyer_share = 0.5
            seller_share = 0.5
            note = "Both elasticities are zero; burden split assumed 50/50 (indeterminate in theory)."
        else:
            # The more inelastic side bears the larger share of a tax burden.
            buyer_share = es / denom
            seller_share = ed / denom
            note = (
                "The relatively inelastic side bears the larger share of the burden "
                "(or captures the larger share of a subsidy benefit)."
            )

        direction_word = "benefit" if is_subsidy else "burden"
        summary = (
            f"For {instrument} in {jurisdiction or 'the specified market'}: buyers bear "
            f"{buyer_share:.1%} and sellers bear {seller_share:.1%} of the {direction_word}. "
            + note
        )

        distributional = [
            {"group": "buyers", "share_or_change": f"{buyer_share:.1%}", "direction": "gain" if is_subsidy else "loss"},
            {"group": "sellers", "share_or_change": f"{seller_share:.1%}", "direction": "gain" if is_subsidy else "loss"},
        ]
        for g in affected_groups:
            distributional.append({"group": g, "share_or_change": "see elasticity assumption", "direction": "context-dependent"})

        welfare = [
            {
                "category": "deadweight loss",
                "description": f"{instrument} introduces a wedge between marginal benefit and marginal cost.",
                "estimated_magnitude": "grows with the size of the wedge and the elasticities",
                "direction": "cost",
                "confidence": "medium",
            }
        ]
        if is_subsidy:
            welfare.append({
                "category": "intended transfer",
                "description": "Subsidy transfers surplus to the targeted side but may overshoot to unintended beneficiaries.",
                "estimated_magnitude": "moderate",
                "direction": "benefit",
                "confidence": "medium",
            })

        caveats = [
            "Incidence depends on elasticities which are empirical estimates, not constants.",
            "General-equilibrium effects (capital mobility, cross-market shifting) are not modelled here.",
            "Statutory incidence (who remits) differs from economic incidence (who bears the burden).",
        ]

        return ToolResult(
            tool=self.name,
            ok=True,
            output={
                "instrument": instrument,
                "jurisdiction": jurisdiction,
                "buyer_share": round(buyer_share, 4),
                "seller_share": round(seller_share, 4),
                "incidence_summary": summary,
                "distributional_effects": distributional,
                "welfare_effects": welfare,
                "caveats": caveats,
            },
        )

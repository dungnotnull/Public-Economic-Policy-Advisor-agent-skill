"""Welfare sub-advisor: market-failure diagnosis and distributional analysis."""

from __future__ import annotations

from config.schema import Citation, DistributionalEffect, PolicyAnalysisReport
from policy_advisor.citations import citations_for, evidence_base_for
from policy_advisor.utils.synthesis import synthesize_narrative
from .base import SubAdvisor


class WelfareAdvisor(SubAdvisor):
    name = "welfare"
    formats = ["market-failure-diagnostic", "policy-memo"]
    keywords = [
        "externality", "public good", "market failure", "information asymmetry",
        "monopoly", "market power", "pollution", "regulation", "distribution",
        "inequality", "equity", "redistribution", "welfare",
    ]

    def handle(self, invocation) -> PolicyAnalysisReport:
        self.ctx.lifecycle.fire(_phase("DELEGATION"), invocation.request_id, {"sub_advisor": self.name})
        ctx = invocation.context
        result = self.ctx.tools.invoke("market_failure_diagnostic", {
            "situation": invocation.user_query,
            "proposed_intervention": ctx.get("proposed_intervention", ""),
        })
        out = result.output
        diagnosed = out["diagnosed_failures"]
        rationale = out["intervention_rationale"]
        recommendations = [r["justified_intervention"] for r in rationale] or [
            "No clear efficiency-based market failure detected; reassess whether intervention is justified."
        ]
        evidence = evidence_base_for(["market-failure", "distribution-redistribution"])
        principles = [
            "Diagnose the specific market failure before justifying intervention (Coase 1960; Samuelson 1954; Akerlof 1970).",
            "Intervention should target the specific failure, not be broader than necessary.",
            "Distributional equity is a value judgement, not a pure efficiency failure - flag it separately.",
        ]
        narrative = synthesize_narrative(
            self.ctx.llm,
            "Market-failure framework (externalities, public goods, information asymmetry, market power, equity)",
            invocation.user_query,
            self._grounded_snippets(["03-market-failure"]),
            principles,
            [c.label for c in evidence],
            "Diagnosed market failure(s): " + (", ".join(f["failure_type"] for f in diagnosed) or "none detected") + ".",
        )
        return PolicyAnalysisReport(
            request_id=invocation.request_id,
            title=invocation.user_query[:80],
            framework_applied="Market-failure framework (externalities, public goods, information asymmetry, market power, equity)",
            jurisdiction=ctx.get("jurisdiction", ""),
            summary=(
                "Diagnosed market failure(s): "
                + (", ".join(f["failure_type"] for f in diagnosed) or "none detected")
                + "."
            ),
            market_failure_diagnosis=[f["failure_type"] for f in diagnosed],
            distributional_effects=[
                DistributionalEffect(group="affected parties", share_or_change="context-dependent", direction="neutral", notes="Distributional impact must be assessed separately from the efficiency case.")
            ],
            recommendations=recommendations,
            uncertainties=out.get("notes", []),
            evidence_base=evidence,
            narrative=narrative,
            citations=citations_for("market-failure", limit=6),
            disclaimer=self._disclaimer(),
        )


def _phase(name: str):
    from ..hooks.lifecycle import LifecyclePhase
    return LifecyclePhase[name]

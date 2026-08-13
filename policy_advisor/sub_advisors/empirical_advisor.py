"""Empirical sub-advisor: causal policy-evaluation method selection."""

from __future__ import annotations

from config.schema import CausalEvaluationReport, Citation, PolicyAnalysisReport
from policy_advisor.citations import citations_for, evidence_base_for
from policy_advisor.utils.synthesis import synthesize_narrative
from .base import SubAdvisor


class EmpiricalAdvisor(SubAdvisor):
    name = "empirical"
    formats = ["causal-evaluation", "policy-memo"]
    keywords = [
        "evaluate", "evaluation", "rct", "randomized", "difference-in-differences",
        "diff-in-diff", "regression discontinuity", "rdd", "instrumental variable",
        "natural experiment", "causal", "impact", "evidence", "empirical",
    ]

    def handle(self, invocation):
        self.ctx.lifecycle.fire(_phase("DELEGATION"), invocation.request_id, {"sub_advisor": self.name})
        ctx = invocation.context
        result = self.ctx.tools.invoke("causal_evaluation", {
            "policy_under_evaluation": invocation.user_query,
            "evaluation_context": ctx.get("evaluation_context", {}),
        })
        out = result.output
        evidence = evidence_base_for(["causal-inference", "macro-schools"])
        principles = [
            "Identification comes from a clean research design, not from correlation (Angrist & Pischke 2009).",
            "RCTs give internal validity but limited external validity; pair them with theory (Deaton 2010).",
            "Watch selection into treatment and endogeneity of shocks (Heckman 1979).",
            "The Lucas critique: behavioural responses may differ under a new regime (Lucas 1976).",
        ]
        narrative = synthesize_narrative(
            self.ctx.llm,
            "Modern causal-evaluation methods (RCT, DiD, RDD, IV, natural experiment)",
            invocation.user_query,
            self._grounded_snippets(["05-causal-inference"]),
            principles,
            [c.label for c in evidence],
            f"Recommended identification strategy: {out['recommended_method']}. {out['method_rationale']}",
        )
        if invocation.requested_format == "causal-evaluation":
            return CausalEvaluationReport(
                request_id=invocation.request_id,
                policy_under_evaluation=out["policy_under_evaluation"],
                recommended_method=out["recommended_method"],
                method_rationale=out["method_rationale"],
                identification_strategy=out["identification_strategy"],
                data_requirements=out["data_requirements"],
                threats_to_validity=out["threats_to_validity"],
                expected_effect_estimate=ctx.get("expected_effect_estimate", "Not specified; estimate empirically once data is available."),
                confidence=out["confidence"],
                evidence_base=evidence,
                narrative=narrative,
                citations=citations_for("causal-inference", limit=6),
                disclaimer=self._disclaimer(),
            )
        # policy-memo path
        return PolicyAnalysisReport(
            request_id=invocation.request_id,
            title=invocation.user_query[:80],
            framework_applied="Modern causal-evaluation methods (RCT, DiD, RDD, IV, natural experiment)",
            jurisdiction=ctx.get("jurisdiction", ""),
            summary=f"Recommended identification strategy: {out['recommended_method']}. {out['method_rationale']}",
            empirical_evidence=[out["identification_strategy"]],
            recommendations=[
                f"Adopt {out['recommended_method']} given the available evaluation context.",
                "Pre-register the analysis and report threats to validity transparently.",
            ],
            uncertainties=out["threats_to_validity"],
            evidence_base=evidence,
            narrative=narrative,
            citations=citations_for("causal-inference", limit=5),
            disclaimer=self._disclaimer(),
        )


def _phase(name: str):
    from ..hooks.lifecycle import LifecyclePhase
    return LifecyclePhase[name]

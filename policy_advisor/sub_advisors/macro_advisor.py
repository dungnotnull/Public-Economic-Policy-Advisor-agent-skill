"""Macro sub-advisor: comparative schools of thought and balanced pro/con debate."""

from __future__ import annotations

from typing import List

from config.schema import Citation, PolicyAnalysisReport, ProConDebateReport, Viewpoint
from policy_advisor.citations import citations_for, evidence_base_for
from policy_advisor.utils.synthesis import synthesize_narrative
from .base import SubAdvisor


class MacroAdvisor(SubAdvisor):
    name = "macro"
    formats = ["pro-con-debate", "policy-memo"]
    keywords = [
        "monetary policy", "inflation", "interest rate", "keynesian", "monetarist",
        "supply-side", "fiscal stimulus", "phillips", "central bank", "schools of thought",
        "recession", "laffer", "new classical",
    ]

    def handle(self, invocation) -> PolicyAnalysisReport | ProConDebateReport:
        if invocation.requested_format == "pro-con-debate":
            return self._handle_debate(invocation)
        return self._handle_memo(invocation)

    def _handle_debate(self, invocation) -> ProConDebateReport:
        self.ctx.lifecycle.fire(_phase("DELEGATION"), invocation.request_id, {"sub_advisor": self.name})
        ctx = invocation.context
        inputs = {"policy_question": invocation.user_query}
        schools = ctx.get("schools")
        if schools:
            inputs["schools"] = schools
        result = self.ctx.tools.invoke("comparative_schools", inputs)
        out = result.output
        viewpoints = [Viewpoint(**v) for v in out["viewpoints"]]
        # Build a balanced pro/con matrix from the first two contrasting schools.
        if len(viewpoints) >= 2:
            a, b = viewpoints[0], viewpoints[1]
            pros_a = [a.key_argument]
            cons_a = [a.caveats] if a.caveats else []
            pros_b = [b.key_argument]
            cons_b = [b.caveats] if b.caveats else []
        else:
            pros_a = pros_b = cons_a = cons_b = []

        evidence = evidence_base_for(["macro-schools", "causal-inference"])
        principles = [
            "Present each school's position, key argument, and caveats (Keynes; Friedman; Lucas; Laffer).",
            "The Lucas critique: structural parameters are not invariant to new policy regimes.",
            "Defer empirical resolution to credible causal-evaluation evidence for the specific context (Rodrik).",
        ]
        narrative = synthesize_narrative(
            self.ctx.llm,
            "Comparative macroeconomic schools (balanced multi-viewpoint)",
            invocation.user_query,
            self._grounded_snippets(["04-macro-schools"]),
            principles,
            [c.label for c in evidence],
            "Evidence on this macroeconomic question is contested across schools.",
        )
        return ProConDebateReport(
            request_id=invocation.request_id,
            question=out["policy_question"],
            stance_a=viewpoints[0].school if viewpoints else "Stance A",
            stance_b=viewpoints[1].school if len(viewpoints) > 1 else "Stance B",
            pros_a=pros_a,
            cons_a=cons_a,
            pros_b=pros_b,
            cons_b=cons_b,
            empirical_resolution=(
                "Empirical resolution depends on context (elasticities, credibility of policy, "
                "and the specific economy); consult causal-evaluation evidence (Angrist & Pischke 2009; "
                "Card & Krueger 1994) rather than treating either school as settled (Lucas 1976; Rodrik 2007)."
            ),
            open_questions=[
                "Which regime best fits the economy's current rigidities and expectations?",
                "How credible is the policy commitment (time-consistency)?",
            ],
            evidence_base=evidence,
            citations=citations_for("macro-schools", limit=5),
            disclaimer=self._disclaimer(),
        )

    def _handle_memo(self, invocation) -> PolicyAnalysisReport:
        self.ctx.lifecycle.fire(_phase("DELEGATION"), invocation.request_id, {"sub_advisor": self.name})
        result = self.ctx.tools.invoke("comparative_schools", {"policy_question": invocation.user_query})
        out = result.output
        viewpoints = [Viewpoint(**v) for v in out["viewpoints"]]
        evidence = evidence_base_for(["macro-schools", "causal-inference"])
        principles = [
            "Never endorse one macro school as settled; present all major viewpoints.",
            "The Lucas critique warns against assuming historical policy-response parameters remain stable.",
            "Where possible, ground the choice in causal-evaluation evidence for the specific context.",
        ]
        narrative = synthesize_narrative(
            self.ctx.llm,
            "Comparative macroeconomic schools (multi-viewpoint)",
            invocation.user_query,
            self._grounded_snippets(["04-macro-schools"]),
            principles,
            [c.label for c in evidence],
            "Evidence on this macroeconomic question is contested across schools.",
        )
        return PolicyAnalysisReport(
            request_id=invocation.request_id,
            title=invocation.user_query[:80],
            framework_applied="Comparative macroeconomic schools (multi-viewpoint)",
            jurisdiction=invocation.context.get("jurisdiction", ""),
            summary=(
                "Evidence on this macroeconomic question is contested across schools; "
                "the answer depends on assumptions about rigidities, expectations, and credibility."
            ),
            viewpoints=viewpoints,
            recommendations=[
                "Present all major schools; do not endorse one as settled.",
                "Where possible, ground the choice in causal-evaluation evidence for the specific context.",
            ],
            uncertainties=["Schools disagree on the magnitude and duration of real effects."],
            evidence_base=evidence,
            narrative=narrative,
            citations=citations_for("macro-schools", limit=5),
            disclaimer=self._disclaimer(),
        )


def _phase(name: str):
    from ..hooks.lifecycle import LifecyclePhase
    return LifecyclePhase[name]

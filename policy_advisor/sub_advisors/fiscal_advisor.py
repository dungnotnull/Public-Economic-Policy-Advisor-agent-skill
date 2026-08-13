"""Fiscal sub-advisor: taxation, subsidies, and cost-benefit analysis."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from config.schema import (
    CostBenefitItem,
    Citation,
    DistributionalEffect,
    PolicyAnalysisReport,
    TaxIncidenceReport,
)
from policy_advisor.citations import citations_for, evidence_base_for
from policy_advisor.utils.synthesis import synthesize_narrative
from .base import SubAdvisor

_NUM = r"[-+]?\d*\.?\d+"


def _parse_float(text: str, default: float = 1.0) -> float:
    m = re.search(_NUM, str(text))
    return float(m.group()) if m else default


class FiscalAdvisor(SubAdvisor):
    name = "fiscal"
    formats = ["tax-incidence", "cost-benefit-analysis", "policy-memo"]
    keywords = [
        "tax", "taxation", "subsidy", "vat", "income tax", "corporate tax",
        "incidence", "cost-benefit", "fiscal", "budget", "spending", "transfer",
    ]

    def handle(self, invocation) -> Any:
        fmt = invocation.requested_format
        if fmt == "tax-incidence":
            return self._handle_incidence(invocation)
        if fmt == "cost-benefit-analysis":
            return self._handle_cba(invocation)
        return self._handle_memo(invocation)

    # ------------------------------------------------------------------ #
    def _handle_incidence(self, invocation) -> TaxIncidenceReport:
        self.ctx.lifecycle.fire(_phase("DELEGATION"), invocation.request_id, {"sub_advisor": self.name})
        query = invocation.user_query
        ctx = invocation.context
        instrument = ctx.get("instrument") or self._infer_instrument(query)
        es = _parse_float(str(ctx.get("supply_elasticity", "1.0")), 1.0)
        ed = _parse_float(str(ctx.get("demand_elasticity", "0.5")), 0.5)
        is_subsidy = bool(ctx.get("is_subsidy", "subsidy" in query.lower()))
        groups = ctx.get("affected_groups", [])

        result = self.ctx.tools.invoke("tax_incidence", {
            "instrument": instrument,
            "jurisdiction": ctx.get("jurisdiction", ""),
            "supply_elasticity": es,
            "demand_elasticity": ed,
            "is_subsidy": is_subsidy,
            "affected_groups": groups,
        })
        out = result.output
        distributional = [DistributionalEffect(**d) for d in out["distributional_effects"]]
        welfare = [CostBenefitItem(**w) for w in out["welfare_effects"]]

        evidence = evidence_base_for(["tax-incidence", "welfare-economics-cba"])
        principles = [
            "Economic incidence depends on relative elasticities, not statutory assignment (Harberger 1962).",
            "The more inelastic side bears the larger share of the burden.",
            "Elasticities are empirical sufficient statistics (Chetty 2009; Saez 2001), not constants.",
        ]
        narrative = synthesize_narrative(
            self.ctx.llm,
            "Harberger-style tax-incidence analysis",
            invocation.user_query,
            self._grounded_snippets(["02-tax-incidence"]),
            principles,
            [c.label for c in evidence],
            out["incidence_summary"],
        )
        return TaxIncidenceReport(
            request_id=invocation.request_id,
            instrument=instrument,
            jurisdiction=out["jurisdiction"],
            statutory_burden=ctx.get("statutory_burden", "Statutory incidence is who legally remits; economic incidence differs (see below)."),
            economic_incidence=distributional,
            elasticity_assumptions=[
                f"supply elasticity assumed = {es}",
                f"demand elasticity assumed = {ed}",
                "Magnitude of the burden share depends on relative elasticities, not statutory assignment.",
            ],
            welfare_effects=welfare,
            distributional_effects=distributional,
            caveats=out["caveats"],
            evidence_base=evidence,
            narrative=narrative,
            citations=citations_for("tax-incidence", limit=6),
            disclaimer=self._disclaimer(),
        )

    # ------------------------------------------------------------------ #
    def _handle_cba(self, invocation) -> PolicyAnalysisReport:
        self.ctx.lifecycle.fire(_phase("DELEGATION"), invocation.request_id, {"sub_advisor": self.name})
        ctx = invocation.context
        items = ctx.get("items") or self._derive_items(invocation.user_query)
        result = self.ctx.tools.invoke("cost_benefit_analysis", {
            "policy_name": ctx.get("policy_name", invocation.user_query[:80]),
            "jurisdiction": ctx.get("jurisdiction", ""),
            "items": items,
            "discount_note": ctx.get("discount_note", ""),
        })
        out = result.output
        scored = [CostBenefitItem(**{k: v for k, v in s.items() if k in CostBenefitItem.__dataclass_fields__}) for s in out["items_scored"]]
        evidence = evidence_base_for(["welfare-economics-cba", "tax-incidence"])
        principles = [
            "Enumerate all affected parties; missing a group is the most common CBA error (Atkinson & Stiglitz 1980).",
            "Weight each item by confidence and use ordinal magnitudes, not fabricated currency.",
            "Distinguish efficiency (Kaldor-Hicks) from equity and report them separately.",
        ]
        narrative = synthesize_narrative(
            self.ctx.llm,
            "Welfare-economics cost-benefit analysis",
            invocation.user_query,
            self._grounded_snippets(["01-welfare-economics-cba"]),
            principles,
            [c.label for c in evidence],
            out["verdict"],
        )
        return PolicyAnalysisReport(
            request_id=invocation.request_id,
            title=out["policy_name"],
            framework_applied="Welfare economics / cost-benefit analysis (weighted magnitude x confidence)",
            jurisdiction=out.get("jurisdiction", ""),
            summary=out["verdict"],
            cost_benefit=scored,
            distributional_effects=[DistributionalEffect(group="see items", share_or_change="varies", direction="neutral", notes="; ".join(out.get("distributional_flags") or []))],
            recommendations=[
                f"Aggregate net welfare score: {out['net_score']}.",
                "Run sensitivity analysis on low-confidence items before finalising.",
            ],
            uncertainties=out.get("uncertainty_flags", []),
            evidence_base=evidence,
            narrative=narrative,
            citations=citations_for("welfare-economics-cba", limit=6),
            disclaimer=self._disclaimer(),
        )

    # ------------------------------------------------------------------ #
    def _handle_memo(self, invocation) -> PolicyAnalysisReport:
        self.ctx.lifecycle.fire(_phase("DELEGATION"), invocation.request_id, {"sub_advisor": self.name})
        ctx = invocation.context
        items = ctx.get("items") or self._derive_items(invocation.user_query)
        cba = self.ctx.tools.invoke("cost_benefit_analysis", {
            "policy_name": ctx.get("policy_name", invocation.user_query[:80]),
            "jurisdiction": ctx.get("jurisdiction", ""),
            "items": items,
        })
        mf = self.ctx.tools.invoke("market_failure_diagnostic", {"situation": invocation.user_query})
        out = cba.output
        scored = [CostBenefitItem(**{k: v for k, v in s.items() if k in CostBenefitItem.__dataclass_fields__}) for s in out["items_scored"]]
        evidence = evidence_base_for(["welfare-economics-cba", "market-failure"])
        principles = [
            "Apply the market-failure framework only where a diagnosed failure justifies intervention (Coase 1960).",
            "Intervention should target the specific failure, not be broader than necessary.",
            "Cost-benefit aggregation uses confidence-weighted ordinal magnitudes.",
        ]
        narrative = synthesize_narrative(
            self.ctx.llm,
            "Cost-benefit analysis + market-failure diagnostic",
            invocation.user_query,
            self._grounded_snippets(["01-welfare-economics-cba", "03-market-failure"]),
            principles,
            [c.label for c in evidence],
            out["verdict"],
        )
        return PolicyAnalysisReport(
            request_id=invocation.request_id,
            title=out["policy_name"],
            framework_applied="Cost-benefit analysis + market-failure diagnostic",
            jurisdiction=ctx.get("jurisdiction", ""),
            summary=out["verdict"],
            market_failure_diagnosis=[f["failure_type"] for f in mf.output["diagnosed_failures"]],
            cost_benefit=scored,
            recommendations=[
                f"Net welfare score: {out['net_score']}.",
                "Address diagnosed market failures with targeted, not blanket, intervention.",
            ],
            uncertainties=out.get("uncertainty_flags", []),
            evidence_base=evidence,
            narrative=narrative,
            citations=citations_for("welfare-economics-cba", limit=4) + citations_for("market-failure", limit=3),
            disclaimer=self._disclaimer(),
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _infer_instrument(query: str) -> str:
        q = query.lower()
        for token in ["corporate income tax", "income tax", "vat", "sales tax", "carbon tax", "property tax", "subsidy", "tax"]:
            if token in q:
                return token
        return "unspecified tax instrument"

    @staticmethod
    def _derive_items(query: str) -> List[Dict[str, Any]]:
        """Best-effort default CBA items when the caller supplies none.

        These are deliberately generic structural default items with qualitative
        magnitudes; the caller is expected to refine them. They keep the tool
        functional and honest rather than fabricating numbers.
        """
        return [
            {"category": "intended benefit", "description": "Primary policy objective described in the request", "estimated_magnitude": "moderate", "direction": "benefit", "confidence": "medium"},
            {"category": "direct fiscal cost", "description": "Budgetary cost of implementation and administration", "estimated_magnitude": "moderate", "direction": "cost", "confidence": "medium"},
            {"category": "deadweight loss", "description": "Efficiency loss from behavioural distortion", "estimated_magnitude": "small", "direction": "cost", "confidence": "low"},
            {"category": "distributional effect", "description": "Net effect on targeted and non-targeted groups", "estimated_magnitude": "moderate", "direction": "benefit", "confidence": "low"},
        ]


def _phase(name: str):
    from ..hooks.lifecycle import LifecyclePhase
    return LifecyclePhase[name]

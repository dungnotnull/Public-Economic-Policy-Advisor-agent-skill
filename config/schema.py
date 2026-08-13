"""Input/output schemas for the Public Economic Policy Advisor skill.

These dataclasses double as the canonical contract between the skill router,
sub-advisors, tools, and any downstream consumer (CLI, API, test harness). A
JSON Schema mirror of the report structures lives under ``assets/schemas/``
and is kept in sync by ``scripts/validate_skill.py``.

Only the standard library is used so the schemas can be serialised anywhere.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# Invocation (skill input)
# --------------------------------------------------------------------------- #
@dataclass
class SkillInvocation:
    """A single request dispatched into the skill runtime."""

    request_id: str
    user_query: str
    requested_format: str = "policy-memo"
    """One of: policy-memo, cost-benefit-analysis, tax-incidence, pro-con-debate,
    causal-evaluation, market-failure-diagnostic."""
    context: Dict[str, Any] = field(default_factory=dict)
    """Free-form caller context (jurisdiction, year, currency, prior assumptions)."""
    feature_overrides: Dict[str, bool] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)


# --------------------------------------------------------------------------- #
# Shared building blocks
# --------------------------------------------------------------------------- #
@dataclass
class Citation:
    source_id: str
    label: str
    relevance: str = "supporting"


@dataclass
class Viewpoint:
    school: str
    position: str
    key_argument: str
    caveats: str = ""


@dataclass
class CostBenefitItem:
    category: str
    description: str
    estimated_magnitude: str
    direction: str  # "benefit" | "cost"
    confidence: str = "medium"  # "low" | "medium" | "high"


@dataclass
class DistributionalEffect:
    group: str
    share_or_change: str
    direction: str  # "gain" | "loss" | "neutral"
    notes: str = ""


# --------------------------------------------------------------------------- #
# Report types
# --------------------------------------------------------------------------- #
@dataclass
class PolicyAnalysisReport:
    """Canonical output for general policy-analysis requests."""

    request_id: str
    title: str
    framework_applied: str
    jurisdiction: str
    summary: str
    market_failure_diagnosis: List[str] = field(default_factory=list)
    cost_benefit: List[CostBenefitItem] = field(default_factory=list)
    distributional_effects: List[DistributionalEffect] = field(default_factory=list)
    viewpoints: List[Viewpoint] = field(default_factory=list)
    empirical_evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    evidence_base: List[Citation] = field(default_factory=list)
    """Research papers backing the frameworks applied (from the citation service)."""
    narrative: str = ""
    """Grounded, persuasive prose synthesizing the analysis (LLM-enriched with deterministic fallback)."""
    citations: List[Citation] = field(default_factory=list)
    disclaimer: str = ""
    generated_at: str = field(default_factory=_utc_now_iso)


@dataclass
class TaxIncidenceReport:
    """Output for tax/subsidy incidence modelling requests."""

    request_id: str
    instrument: str  # e.g. "corporate income tax", "VAT", "subsidy"
    jurisdiction: str
    statutory_burden: str
    economic_incidence: List[DistributionalEffect] = field(default_factory=list)
    elasticity_assumptions: List[str] = field(default_factory=list)
    welfare_effects: List[CostBenefitItem] = field(default_factory=list)
    distributional_effects: List[DistributionalEffect] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    evidence_base: List[Citation] = field(default_factory=list)
    narrative: str = ""
    citations: List[Citation] = field(default_factory=list)
    disclaimer: str = ""
    generated_at: str = field(default_factory=_utc_now_iso)


@dataclass
class ProConDebateReport:
    """Balanced pro/con presentation for contested policy debates."""

    request_id: str
    question: str
    stance_a: str
    stance_b: str
    pros_a: List[str] = field(default_factory=list)
    cons_a: List[str] = field(default_factory=list)
    pros_b: List[str] = field(default_factory=list)
    cons_b: List[str] = field(default_factory=list)
    empirical_resolution: str = ""
    open_questions: List[str] = field(default_factory=list)
    evidence_base: List[Citation] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    disclaimer: str = ""
    generated_at: str = field(default_factory=_utc_now_iso)


@dataclass
class CausalEvaluationReport:
    """Output for empirical / causal-evaluation requests."""

    request_id: str
    policy_under_evaluation: str
    recommended_method: str  # "RCT" | "DiD" | "RDD" | "IV" | "natural experiment"
    method_rationale: str
    identification_strategy: str
    data_requirements: List[str] = field(default_factory=list)
    threats_to_validity: List[str] = field(default_factory=list)
    expected_effect_estimate: str = ""
    confidence: str = "low"
    evidence_base: List[Citation] = field(default_factory=list)
    narrative: str = ""
    citations: List[Citation] = field(default_factory=list)
    disclaimer: str = ""
    generated_at: str = field(default_factory=_utc_now_iso)


# --------------------------------------------------------------------------- #
# Result envelope (skill output)
# --------------------------------------------------------------------------- #
@dataclass
class SkillResult:
    """Envelope wrapping any report plus execution metadata."""

    request_id: str
    status: str  # "ok" | "degraded" | "error"
    format: str
    payload: Dict[str, Any]
    route_taken: str = ""
    sub_advisors_used: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    tokens_used: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = ""
    generated_at: str = field(default_factory=_utc_now_iso)

    @classmethod
    def from_report(cls, report: Any, route_taken: str = "", sub_advisors_used: Optional[List[str]] = None, tools_used: Optional[List[str]] = None, warnings: Optional[List[str]] = None) -> "SkillResult":
        return cls(
            request_id=getattr(report, "request_id", ""),
            status="ok",
            format=type(report).__name__,
            payload=asdict(report),
            route_taken=route_taken,
            sub_advisors_used=sub_advisors_used or [],
            tools_used=tools_used or [],
            warnings=warnings or [],
            disclaimer=getattr(report, "disclaimer", ""),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

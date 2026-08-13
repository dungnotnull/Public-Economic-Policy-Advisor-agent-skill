"""Rubric-based evaluation harness for skill outputs.

Runs the standard prompt battery and scores each ``SkillResult`` against an
explicit rubric, producing a 0-100 score per case and an overall pass/fail.
Intended for the skill-creator evaluate/iterate loop and for CI quality
gating. Uses the offline ``MockLLMAdapter`` so it runs with no external deps.

Rubric dimensions (each 0 or max points):
  - framework_named      (15): a named framework is applied.
  - disclaimer_present   (15): the standing disclaimer is present and non-empty.
  - citation_grounding   (20): evidence_base is non-empty (research-grounded).
  - narrative_present    (15): a grounded narrative paragraph is present.
  - structured_payload   (15): payload has the expected report-specific fields.
  - multi_viewpoint      (10): (pro-con only) >= 2 viewpoints / balanced stances.
  - tools_used           (10): at least one framework tool was invoked.

Usage:
    python -m scripts.evaluate_outputs
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from policy_advisor import advise, reset_registry
from policy_advisor.utils.context import MockLLMAdapter

CASES = [
    {"query": "Who really bears the burden of a 20% corporate income tax?", "fmt": "tax-incidence", "context": {"supply_elasticity": 1.5, "demand_elasticity": 0.4}, "expect": ["instrument", "economic_incidence"]},
    {"query": "Is building a new highway worth it?", "fmt": "cost-benefit-analysis", "context": {}, "expect": ["cost_benefit", "framework_applied"]},
    {"query": "Should the government regulate coal pollution to fix a negative externality?", "fmt": "market-failure-diagnostic", "context": {"proposed_intervention": "emissions cap"}, "expect": ["market_failure_diagnosis"]},
    {"query": "Compare Keynesian vs monetarist views on fiscal stimulus during a recession.", "fmt": "pro-con-debate", "context": {}, "expect": ["stance_a", "stance_b"], "multi_viewpoint": True},
    {"query": "How should we evaluate the impact of a job-training program?", "fmt": "causal-evaluation", "context": {"evaluation_context": {"can_randomize": True}}, "expect": ["recommended_method", "threats_to_validity"]},
    {"query": "Analyse a proposed universal basic income funded by a VAT.", "fmt": "policy-memo", "context": {"jurisdiction": "Country Z"}, "expect": ["framework_applied"]},
]

WEIGHTS = {"framework_named": 15, "disclaimer_present": 15, "citation_grounding": 20, "narrative_present": 15, "structured_payload": 15, "multi_viewpoint": 10, "tools_used": 10}


def score_case(case, result) -> tuple[int, dict[str, int]]:
    p = result.payload
    s = {"framework_named": 0, "disclaimer_present": 0, "citation_grounding": 0, "narrative_present": 0, "structured_payload": 0, "multi_viewpoint": 0, "tools_used": 0}
    if p.get("framework_applied") or p.get("method_rationale"):
        s["framework_named"] = WEIGHTS["framework_named"]
    if result.disclaimer and "not professional advice" in result.disclaimer:
        s["disclaimer_present"] = WEIGHTS["disclaimer_present"]
    if p.get("evidence_base"):
        s["citation_grounding"] = WEIGHTS["citation_grounding"]
    if p.get("narrative") or (case["fmt"] == "pro-con-debate" and p.get("empirical_resolution")):
        s["narrative_present"] = WEIGHTS["narrative_present"]
    if all(p.get(f) is not None for f in case["expect"]):
        s["structured_payload"] = WEIGHTS["structured_payload"]
    if case.get("multi_viewpoint"):
        if p.get("stance_a") and p.get("stance_b") and p["stance_a"] != p["stance_b"] and p.get("pros_a") and p.get("pros_b"):
            s["multi_viewpoint"] = WEIGHTS["multi_viewpoint"]
    else:
        # Cases that do not require multi-viewpoint get these points by default.
        s["multi_viewpoint"] = WEIGHTS["multi_viewpoint"]
    if result.tools_used:
        s["tools_used"] = WEIGHTS["tools_used"]
    return sum(s.values()), s


def main() -> int:
    reset_registry()
    total = 0
    max_total = 0
    print("[evaluate_outputs] rubric scoring")
    for case in CASES:
        result = advise(user_query=case["query"], requested_format=case["fmt"], context=case["context"], llm=MockLLMAdapter())
        score, breakdown = score_case(case, result)
        total += score
        max_total += sum(WEIGHTS.values())
        print(f"  {score:>3}/100  [{result.route_taken:<8}] {case['fmt']:<22} {breakdown}")
    pct = round(100.0 * total / max_total, 1) if max_total else 0.0
    print(f"[evaluate_outputs] overall: {total}/{max_total} ({pct}%)")
    return 0 if pct >= 90.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

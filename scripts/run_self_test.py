"""Run the skill's self-test prompt suite.

Executes a fixed battery of representative prompts across every output format
and sub-advisor, asserts that each returns a non-degraded ``SkillResult``
bearing the mandatory disclaimer, and prints a summary. Uses the offline
``MockLLMAdapter`` so the suite runs with no external dependencies.

Usage:
    python -m scripts.run_self_test
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
    {
        "name": "tax-incidence (fiscal)",
        "query": "Who really bears the burden of a 20% corporate income tax?",
        "fmt": "tax-incidence",
        "context": {"supply_elasticity": 1.5, "demand_elasticity": 0.4, "jurisdiction": "Country X"},
    },
    {
        "name": "cost-benefit (fiscal)",
        "query": "Is building a new highway worth it?",
        "fmt": "cost-benefit-analysis",
        "context": {"jurisdiction": "Region Y"},
    },
    {
        "name": "market-failure (welfare)",
        "query": "Should the government regulate coal pollution to fix a negative externality?",
        "fmt": "market-failure-diagnostic",
        "context": {"proposed_intervention": "emissions cap"},
    },
    {
        "name": "pro-con (macro)",
        "query": "Compare Keynesian vs monetarist views on fiscal stimulus during a recession.",
        "fmt": "pro-con-debate",
        "context": {},
    },
    {
        "name": "causal-evaluation (empirical)",
        "query": "How should we evaluate the impact of a job-training program?",
        "fmt": "causal-evaluation",
        "context": {"evaluation_context": {"can_randomize": True, "has_panel_data": True}},
    },
    {
        "name": "policy-memo default (welfare)",
        "query": "Analyse a proposed universal basic income funded by a VAT.",
        "fmt": "policy-memo",
        "context": {"jurisdiction": "Country Z"},
    },
]


def main() -> int:
    reset_registry()
    failures: list[str] = []
    for case in CASES:
        result = advise(
            user_query=case["query"],
            requested_format=case["fmt"],
            context=case["context"],
            llm=MockLLMAdapter(),
        )
        ok = result.status == "ok" and bool(result.disclaimer)
        line = f"  [{'PASS' if ok else 'FAIL'}] {case['name']} -> status={result.status}, route={result.route_taken}, tools={result.tools_used}"
        print(line)
        if not ok:
            failures.append(case["name"])
            print(f"      warnings: {result.warnings}")

    print()
    if failures:
        print(f"[self_test] {len(failures)} case(s) failed: {failures}")
        return 1
    print(f"[self_test] OK - all {len(CASES)} cases passed with disclaimer present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

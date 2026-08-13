"""Command-line entry point for the Public Economic Policy Advisor skill.

Usage:
    python -m policy_advisor --query "Who bears a 20% corporate income tax?" \
        --format tax-incidence --context '{"supply_elasticity": 1.5, "demand_elasticity": 0.4}'

Without arguments it runs the built-in self-test battery.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

from . import advise


def _parse_context(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--context must be valid JSON: {exc}") from exc


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pepa",
        description="Public Economic Policy Advisor - structured public-economics policy analysis.",
    )
    parser.add_argument("--query", "-q", help="The policy question to analyse.")
    parser.add_argument(
        "--format",
        "-f",
        default="policy-memo",
        choices=["policy-memo", "cost-benefit-analysis", "tax-incidence", "pro-con-debate", "causal-evaluation", "market-failure-diagnostic"],
        help="Requested output format (default: policy-memo).",
    )
    parser.add_argument("--context", "-c", help="JSON object with extra context (jurisdiction, elasticities, items, ...).")
    parser.add_argument("--provider", choices=["auto", "anthropic", "openai", "mock"], default=None,
        help="LLM provider to use (overrides PEPA_LLM_PROVIDER / settings).")
    parser.add_argument("--request-id", help="Optional request id.")
    args = parser.parse_args(argv)

    if args.provider:
        import os
        os.environ["PEPA_LLM_PROVIDER"] = args.provider

    if not args.query:
        # No query: run the self-test battery so the CLI is useful out of the box.
        from scripts.run_self_test import main as run_self_test
        return run_self_test()

    result = advise(
        user_query=args.query,
        requested_format=args.format,
        context=_parse_context(args.context),
        request_id=args.request_id,
    )
    print(result.to_json())
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

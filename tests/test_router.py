"""Tests for the chain-of-thought router and sub-advisor resolution."""

import pytest

from config.schema import SkillInvocation
from policy_advisor.router import ChainOfThoughtRouter
from policy_advisor.sub_advisors import (
    EmpiricalAdvisor,
    FiscalAdvisor,
    MacroAdvisor,
    WelfareAdvisor,
)
from policy_advisor.tools import ToolRegistry, register_default_tools
from policy_advisor.utils.context import MockLLMAdapter


def _build_router():
    from policy_advisor.sub_advisors import SubAdvisorContext
    ctx = SubAdvisorContext(tools=ToolRegistry(), llm=MockLLMAdapter())
    register_default_tools(ctx.tools)
    advisors = [FiscalAdvisor(ctx), MacroAdvisor(ctx), WelfareAdvisor(ctx), EmpiricalAdvisor(ctx)]
    return ChainOfThoughtRouter(advisors), advisors


def _inv(fmt, query):
    return SkillInvocation(request_id="t", user_query=query, requested_format=fmt)


def test_explicit_format_match_fiscal():
    router, _ = _build_router()
    decision = router.route(_inv("tax-incidence", "who pays the tax?"))
    assert decision.sub_advisor == "fiscal"
    assert any("format match" in r for r in decision.reasoning)


def test_explicit_format_match_macro():
    router, _ = _build_router()
    assert router.route(_inv("pro-con-debate", "stimulus debate")).sub_advisor == "macro"


def test_explicit_format_match_welfare():
    router, _ = _build_router()
    assert router.route(_inv("market-failure-diagnostic", "pollution")).sub_advisor == "welfare"


def test_explicit_format_match_empirical():
    router, _ = _build_router()
    assert router.route(_inv("causal-evaluation", "evaluate program")).sub_advisor == "empirical"


def test_keyword_fallback_when_format_unmatched():
    router, _ = _build_router()
    # Unknown format but strong fiscal keywords -> fiscal via keyword fallback.
    decision = router.route(_inv("custom-format", "analyse the incidence of a new corporate income tax"))
    assert decision.sub_advisor == "fiscal"


def test_default_to_welfare_for_open_memo():
    router, _ = _build_router()
    decision = router.route(_inv("policy-memo", "what should we do about the economy?"))
    assert decision.sub_advisor == "welfare"


def test_resolve_returns_matching_sub_advisor():
    router, advisors = _build_router()
    chosen = router.resolve(_inv("tax-incidence", "tax"))
    assert isinstance(chosen, FiscalAdvisor)


def test_keyword_tiebreak_among_format_matches():
    router, _ = _build_router()
    # Both fiscal and welfare serve policy-memo; fiscal keywords dominate a tax query.
    decision = router.route(_inv("policy-memo", "analyse a new corporate income tax and its incidence"))
    assert decision.sub_advisor == "fiscal"

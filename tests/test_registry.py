"""Tests for the SkillRegistry end-to-end orchestration and report outputs."""

import json

import pytest

from policy_advisor import advise, reset_registry
from config.schema import SkillResult
from policy_advisor.skill_registry import SkillRegistry
from policy_advisor.utils.context import MockLLMAdapter


@pytest.fixture(autouse=True)
def _reset():
    reset_registry()
    yield
    reset_registry()


def test_advise_tax_incidence_returns_ok_with_disclaimer():
    result = advise(
        "Who bears a 20% corporate income tax?",
        requested_format="tax-incidence",
        context={"supply_elasticity": 1.5, "demand_elasticity": 0.4, "jurisdiction": "X"},
    )
    assert result.status == "ok"
    assert result.route_taken == "fiscal"
    assert "tax_incidence" in result.tools_used
    assert "not professional advice" in result.disclaimer
    payload = json.loads(result.to_json())["payload"]
    assert payload["instrument"] == "corporate income tax"
    buyers = next(e for e in payload["economic_incidence"] if e["group"] == "buyers")
    # Supply elastic (1.5), demand inelastic (0.4) -> buyers bear the larger share.
    assert float(buyers["share_or_change"].rstrip("%")) > 50.0


def test_advise_market_failure_diagnoses_externality():
    result = advise("regulate coal pollution externality", requested_format="market-failure-diagnostic")
    assert result.status == "ok"
    assert result.route_taken == "welfare"
    assert "negative_externality" in result.payload["market_failure_diagnosis"]


def test_advise_pro_con_returns_viewpoints():
    result = advise("Keynesian vs monetarist stimulus", requested_format="pro-con-debate")
    assert result.status == "ok"
    assert result.route_taken == "macro"
    assert len(result.payload["pros_a"]) >= 1
    assert result.payload["stance_a"] != result.payload["stance_b"]


def test_advise_causal_evaluation_picks_method():
    result = advise(
        "evaluate a job training program",
        requested_format="causal-evaluation",
        context={"evaluation_context": {"can_randomize": True}},
    )
    assert result.status == "ok"
    assert result.route_taken == "empirical"
    assert result.payload["recommended_method"] == "RCT"


def test_advise_default_memo():
    result = advise("analyse a universal basic income funded by VAT", requested_format="policy-memo")
    assert result.status == "ok"
    assert result.payload["framework_applied"]


def test_degraded_result_on_routing_failure_is_recoverable():
    registry = SkillRegistry(llm=MockLLMAdapter())
    registry.initialize()
    from config.schema import SkillInvocation
    # Force a routing error by clearing sub-advisors but keeping the router empty.
    registry.sub_advisors = []
    registry.router = None
    from policy_advisor.router import ChainOfThoughtRouter
    registry.router = ChainOfThoughtRouter([])
    inv = SkillInvocation(request_id="x", user_query="anything", requested_format="policy-memo")
    result = registry.invoke(inv)
    assert result.status in {"degraded", "error"}
    assert result.disclaimer  # disclaimer still present even when degraded


def test_skill_result_serialises_to_valid_json():
    result = advise("carbon tax", requested_format="market-failure-diagnostic")
    data = json.loads(result.to_json())
    assert data["status"] == "ok"
    assert data["request_id"] == result.request_id


def test_state_store_persists_invocation():
    result = advise("subsidy incidence", requested_format="tax-incidence", context={"supply_elasticity": 1.0, "demand_elasticity": 1.0, "is_subsidy": True})
    from policy_advisor.skill_registry import get_registry
    stored = get_registry().state.get(result.request_id)
    assert stored is not None
    assert json.loads(stored)["status"] == "ok"
